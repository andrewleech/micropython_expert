# ROMFS Board Configuration Guide

This document provides comprehensive guidance for board profile developers on how to add ROMFS (Read-Only Memory File System) support to MicroPython boards.

## Overview

ROMFS allows embedding a read-only filesystem directly in flash memory that can be accessed at runtime through the `/rom` mount point. This feature enables:

- Fast access to Python modules and data files (faster than FAT/LittleFS)
- Deployment of applications and libraries without modifying firmware
- Runtime updates of ROM content via `vfs.rom_ioctl()` and `mpremote`

## Core Requirements

### 1. Enable ROMFS Support

Add these defines to your board's `mpconfigboard.h`:

```c
#define MICROPY_VFS_ROM (1)
```

This automatically enables `MICROPY_VFS_ROM_IOCTL` unless explicitly disabled.

**Note:** When both `MICROPY_VFS_ROM` and `MICROPY_VFS_ROM_IOCTL` are enabled, ROMFS will be automatically mounted at `/rom` during `mp_init()`. Both `/rom` and `/rom/lib` are added to `sys.path`.

### 2. Implement Port-Specific rom_ioctl Function

Each port must implement `mp_vfs_rom_ioctl()` in a `vfs_rom_ioctl.c` file. This function handles:

- `MP_VFS_ROM_IOCTL_GET_NUMBER_OF_SEGMENTS` - Query number of ROM partitions
- `MP_VFS_ROM_IOCTL_GET_SEGMENT` - Get partition info (address, size)
- `MP_VFS_ROM_IOCTL_WRITE_PREPARE` - Prepare partition for writing (erase)
- `MP_VFS_ROM_IOCTL_WRITE` - Write data to partition
- `MP_VFS_ROM_IOCTL_WRITE_COMPLETE` - Finalize write operation

## Port-Specific Implementation Patterns

### STM32 Port

**Configuration Options:**

```c
// For internal flash storage
#define MICROPY_HW_ROMFS_ENABLE_INTERNAL_FLASH (1)

// For external QSPI flash storage  
#define MICROPY_HW_ROMFS_ENABLE_EXTERNAL_QSPI (1)
#define MICROPY_HW_ROMFS_QSPI_SPIFLASH_OBJ (&spi_bdev_obj)

// Enable partitions (up to 2 supported)
#define MICROPY_HW_ROMFS_ENABLE_PART0 (1)
#define MICROPY_HW_ROMFS_ENABLE_PART1 (1)  // Optional second partition
```

**Linker Script Requirements:**

Define partition symbols in your `.ld` file:

```ld
MEMORY
{
    /* Other memory regions... */
    FLASH_ROMFS (rx): ORIGIN = 0x90000000, LENGTH = 1024K
}

/* ROMFS location symbols */
_micropy_hw_romfs_part0_start = ORIGIN(FLASH_ROMFS);
_micropy_hw_romfs_part0_size = LENGTH(FLASH_ROMFS);

/* Optional second partition */
_micropy_hw_romfs_part1_start = ORIGIN(FLASH_ROMFS2);
_micropy_hw_romfs_part1_size = LENGTH(FLASH_ROMFS2);
```

**Example Boards:**
- **PYBD_SF2/SF6**: Uses external QSPI flash, 1MB partition
- **ARDUINO_GIGA**: External QSPI flash support
- **ARDUINO_NICLA_VISION**: External QSPI flash support  
- **ARDUINO_PORTENTA_H7**: External QSPI flash support

### RP2 Port

**Configuration:**

Add to `mpconfigboard.h`:

```c
#define MICROPY_HW_ROMFS_BYTES (128 * 1024)  // Size in bytes
```

**Memory Layout:**
- ROMFS partition placed at end of firmware allocation
- Lives between firmware and read/write filesystem
- Reduces available firmware space by `MICROPY_HW_ROMFS_BYTES`

**Automatic Enablement:**

```c
#define MICROPY_VFS_ROM (MICROPY_HW_ROMFS_BYTES > 0)
```

### ESP32 Port

**Configuration:**

Add to `mpconfigboard.h`:

```c
#define MICROPY_VFS_ROM (1)
```

**Partition Table:**

Create or modify partition CSV file with `romfs` entry:

```csv
# Name,   Type, SubType, Offset,  Size, Flags
nvs,      data, nvs,     0x9000,  0x6000,
phy_init, data, phy,     0xf000,  0x1000,
factory,  app,  factory, 0x10000, 0x1D0000,
romfs,    data, 0x8f,    0x1E0000, 0x20000,    # 128KB ROM partition
vfs,      data, fat,     0x200000, 0x200000,
```

**Board Configuration:**

Specify partition file in board makefile:

```make
PART_SRC = partitions-4MiB-romfs.csv
```

### ESP8266 Port

**Configuration:**

Add to board variant makefile:

```make
CFLAGS += -DMICROPY_VFS_ROM=1
```

**Linker Script:**

Define `FLASH_ROMFS` memory region and symbols:

```ld
MEMORY
{
    /* Other regions... */
    irom0_0_seg :  org = 0x40209000, len = 1M - 36K - 320K  # Reduced firmware space
    FLASH_ROMFS :  org = 0x402b0000, len = 320K             # ROM partition
}

/* ROMFS symbols */
_micropy_hw_romfs_part0_start = ORIGIN(FLASH_ROMFS);
_micropy_hw_romfs_part0_size = LENGTH(FLASH_ROMFS);
```

### Alif Port

**Configuration:**

Add to `mpconfigport.h`:

```c
#define MICROPY_VFS_ROM (1)
```

**Hardware Support:**
- OSPI flash memory (external)
- MRAM (Magnetoresistive RAM) memory
- Up to 2 partitions supported
- Similar partition configuration to STM32

**Configuration Options:**

```c
// Enable partitions
#define MICROPY_HW_ROMFS_ENABLE_PART0 (1)
#define MICROPY_HW_ROMFS_ENABLE_PART1 (1)  // Optional second partition
```

**Linker Script:**

Similar to STM32, define partition symbols:

```ld
/* ROMFS location symbols */
_micropy_hw_romfs_part0_start = ORIGIN(FLASH_ROMFS);
_micropy_hw_romfs_part0_size = LENGTH(FLASH_ROMFS);
```

**Key Features:**
- Automatic detection of OSPI vs MRAM based on memory addresses
- Support for both XIP (execute-in-place) and memory-mapped access
- Hardware-specific address validation for memory safety

## Implementation Checklist

### Required Files

1. **`vfs_rom_ioctl.c`** - Port-specific ROM I/O control implementation
2. **Board configuration** - Add ROMFS defines to `mpconfigboard.h`
3. **Memory layout** - Update linker script or partition table
4. **Build integration** - Add `vfs_rom_ioctl.c` to port Makefile

### Key Implementation Points

1. **Partition Management:**
   - Support 1-2 partitions per port capabilities
   - Expose partition info via `mp_obj_array_t` structures
   - Handle partition bounds checking

2. **Flash Operations:**
   - Implement erase before write
   - Support incremental writes with offset
   - Handle flash-specific alignment requirements
   - Provide proper error handling

3. **Memory Safety:**
   - Validate write boundaries
   - Check partition sizes and alignment
   - Prevent corruption of adjacent areas

4. **Performance Considerations:**
   - ROMFS stat operations are significantly faster than FAT/LittleFS
   - Automatically added to `sys.path` as `/rom` and `/rom/lib`
   - Minimal import overhead compared to frozen modules

## Testing and Validation

### Basic Functionality Test

```python
import vfs

# Query available ROM segments
num_segments = vfs.rom_ioctl(1)
print(f"Available ROM segments: {num_segments}")

# Get segment info
if num_segments > 0:
    segment_info = vfs.rom_ioctl(2, 0)  # Get first segment
    print(f"Segment 0: {segment_info}")
```

### Deployment Test

```bash
# Create and deploy ROMFS via mpremote
mpremote romfs build lib/ --output romfs.img
mpremote romfs deploy romfs.img
```

### Runtime Access Test

```python
import os
print("ROM filesystem contents:")
for item in os.listdir('/rom'):
    print(f"  {item}")
```

## Common Pitfalls

1. **Insufficient Flash Space:** Ensure adequate flash allocation for ROM partition
2. **Alignment Issues:** Respect flash sector/page alignment requirements  
3. **Linker Symbol Errors:** Properly define partition start/size symbols
4. **Missing Dependencies:** Include required flash driver headers
5. **Partition Overlap:** Avoid conflicts with firmware or filesystem areas

## Best Practices

1. **Size Planning:** Reserve 64KB-1MB for typical applications
2. **Partition Layout:** Place ROM between firmware and R/W filesystem
3. **Error Handling:** Implement comprehensive error checking in rom_ioctl
4. **Documentation:** Document partition layout in board documentation
5. **Testing:** Validate on actual hardware with various file sizes

## Port Status (June 2025)

| Port       | Status      | Implementation File | Notes |
|------------|-------------|-------------------|-------|
| STM32      | ✅ Complete | `vfs_rom_ioctl.c` | Internal + External flash |
| RP2        | ✅ Complete | `rp2_flash.c`     | External flash only |
| ESP32      | ✅ Complete | `esp32_partition.c` | Partition table based |
| ESP8266    | ✅ Complete | `vfs_rom_ioctl.c` | External flash only |
| Alif       | ✅ Complete | `vfs_rom_ioctl.c` | OSPI + MRAM support (NEW) |
| UNIX       | ✅ Complete | `main.c`          | Coverage testing only |
| QEMU       | ✅ Complete | -                 | VFS_ROM enabled, no ioctl |
| SAMD       | ❌ Missing  | -                 | Port from PR #8381 |
| MIMXRT     | ❌ Missing  | -                 | Port from PR #8381 |
| NRF        | ❌ Missing  | -                 | Port from PR #8381 |
| RENESAS-RA | ❌ Missing  | -                 | Port from PR #8381 |
| Zephyr     | ❌ Missing  | -                 | No implementation |
| WebAssembly| ❌ Missing  | -                 | No implementation |

This guide provides the foundation for implementing ROMFS support on any MicroPython port. Refer to existing implementations for port-specific patterns and adapt as needed for your target hardware.