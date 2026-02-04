# MicroPython New Port Development Guide

This comprehensive guide walks through creating a new MicroPython port. The guide uses the minimal port as the simplest reference implementation and the STM32 port as a comprehensive example. Recent port development patterns were analyzed from the Alif port's commit progression.

## Overview

A MicroPython port adapts the core MicroPython runtime to a specific hardware platform. This involves:
- **Hardware Abstraction Layer (HAL)**: Interfacing with hardware-specific drivers
- **Build System**: Integrating with toolchains and hardware SDKs  
- **Board Support**: Defining board-specific configurations
- **Peripheral Support**: Implementing machine module interfaces for hardware peripherals

## Prerequisites

Before starting, ensure you have:
- Target hardware documentation and SDK/drivers
- Cross-compilation toolchain (typically `arm-none-eabi-` for ARM Cortex-M)
- Understanding of your hardware's memory layout, peripherals, and boot process
- MicroPython source code and build environment

## Development Phases

Most successful ports follow this logical progression:
1. **Foundation** - Core infrastructure and basic I/O
2. **System Services** - Timing, interrupts, memory management
3. **Peripheral Support** - Progressive addition of hardware interfaces
4. **Advanced Features** - Multi-core, networking, etc.

---

## Phase 1: Foundation (Essential Files)

### Step 1: Create Port Directory Structure

```bash
mkdir ports/YOUR_PORT
cd ports/YOUR_PORT
```

Create these essential directories:
- `boards/` - Board-specific configurations
- `mcu/` - MCU-specific files (linker scripts, pin definitions)
- `modules/` - Port-specific Python modules

### Step 2: Core Configuration Files

#### A. `mpconfigport.h` (Port Configuration)

**Purpose**: Defines which MicroPython features are enabled for your port.

**Common Pattern Analysis**:
- All ports include `mpconfigboard.h` for board-specific overrides
- Use `MICROPY_CONFIG_ROM_LEVEL` for feature sets (MINIMAL/BASIC/EXTRA/FULL)
- Define platform string: `#define MICROPY_PY_SYS_PLATFORM "yourport"`

**Minimal Configuration (from minimal port)**:
```c
// Minimal port uses the simplest possible configuration
#define MICROPY_CONFIG_ROM_LEVEL (MICROPY_CONFIG_ROM_LEVEL_MINIMUM)

// Type definitions - minimal port uses standard C types
typedef int32_t mp_int_t;
typedef uint32_t mp_uint_t;
typedef long mp_off_t;

// Required for all ports
#define MICROPY_HW_BOARD_NAME "minimal"
#define MICROPY_HW_MCU_NAME "unknown-cpu"
```

**Full-Featured Configuration (STM32 port pattern)**:
```c
// STM32 port uses feature levels based on available flash/RAM
#include <stdint.h>
#include <alloca.h>
#include "mpconfigboard.h"
#include "stm32_hal.h"  // Your hardware HAL

// Feature level (STM32 uses different levels for different chips)
#ifndef MICROPY_CONFIG_ROM_LEVEL
#define MICROPY_CONFIG_ROM_LEVEL (MICROPY_CONFIG_ROM_LEVEL_EXTRA_FEATURES)
#endif

// Type definitions (STM32 pattern)
typedef intptr_t mp_int_t;   // must be pointer size
typedef uintptr_t mp_uint_t; // must be pointer size
typedef intptr_t mp_off_t;   // type for offsets

// Python features (STM32 enables based on flash size)
#define MICROPY_ENABLE_GC                       (1)
#define MICROPY_HELPER_REPL                     (1)
#define MICROPY_REPL_AUTO_INDENT                (1)
#define MICROPY_LONGINT_IMPL                    (MICROPY_LONGINT_IMPL_MPZ)

// Hardware features (STM32 pattern)
#define MICROPY_HW_ENABLE_RTC                   (1)
#define MICROPY_HW_ENABLE_ADC                   (1)
#define MICROPY_HW_ENABLE_DAC                   (1)
#define MICROPY_HW_ENABLE_USB                   (1)
#define MICROPY_HW_HAS_SWITCH                   (1)

// Extended modules (STM32 includes many by default)
#define MICROPY_PY_MACHINE                      (1)
#define MICROPY_PY_MACHINE_PIN_BASE             (1)
#define MICROPY_PY_MACHINE_PULSE                (1)
#define MICROPY_PY_MACHINE_I2C                  (1)
#define MICROPY_PY_MACHINE_SPI                  (1)
#define MICROPY_PY_MACHINE_INCLUDEFILE          "ports/stm32/modmachine.c"

// Board hooks (define these as no-ops initially)
#ifndef MICROPY_BOARD_STARTUP
#define MICROPY_BOARD_STARTUP()
#endif

#ifndef MICROPY_BOARD_EARLY_INIT  
#define MICROPY_BOARD_EARLY_INIT()
#endif
```

#### B. `mpconfigport.mk` (Build Configuration)

**Purpose**: Makefile variables for the port.

```makefile
# MicroPython features
MICROPY_VFS_FAT = 1
MICROPY_VFS_LFS2 = 1

# Optimization
COPT = -Os -DNDEBUG

# Floating point
MICROPY_FLOAT_IMPL = double
```

#### C. `qstrdefsport.h` (Port-Specific Strings)

**Purpose**: Define port-specific interned strings (QSTRs).

```c
// qstr definitions for this port

// Example entries:
// Q(Pin)
// Q(UART)
// Q(I2C)
```

### Step 3: Hardware Abstraction Layer

#### A. `mphalport.h` (HAL Interface)

**Purpose**: Defines the hardware abstraction interface.

**Common Pattern**: All ports define these core macros:
- `MICROPY_BEGIN_ATOMIC_SECTION()` / `MICROPY_END_ATOMIC_SECTION()`
- Pin manipulation macros
- Timing functions

**Minimal HAL (from minimal port)**:
```c
// Minimal port shows the bare minimum required
static inline void mp_hal_set_interrupt_char(char c) {}

// Required timing functions (minimal stubs)
static inline mp_uint_t mp_hal_ticks_ms(void) { return 0; }
static inline void mp_hal_delay_ms(mp_uint_t ms) { (void)ms; }
```

**Full HAL (STM32 pattern)**:
```c
#include "py/mphal.h"
#include STM32_HAL_H

// STM32 uses the HAL's critical section functions
#define MICROPY_BEGIN_ATOMIC_SECTION()     disable_irq()
#define MICROPY_END_ATOMIC_SECTION(state)  enable_irq(state)

// STM32 implements proper timing using SysTick
extern volatile uint32_t systick_ms;
static inline mp_uint_t mp_hal_ticks_ms(void) {
    return systick_ms;
}

// STM32 pin handling
#define mp_hal_pin_obj_t const pin_obj_t*
#define mp_hal_get_pin_obj(o)   pin_find(o)
#define mp_hal_pin_od_low(p)    mp_hal_pin_low(p)
#define mp_hal_pin_od_high(p)   mp_hal_pin_high(p)
```

#### B. `mphalport.c` (HAL Implementation)

**Purpose**: Implements the hardware abstraction functions.

**Key Functions to Implement**:

**From minimal port (bare minimum)**:
```c
void mp_hal_stdout_tx_strn(const char *str, size_t len) {
    // Minimal: just write to UART
    for (size_t i = 0; i < len; ++i) {
        uart_tx_char(str[i]);
    }
}
```

**From STM32 port (full implementation)**:
```c
void mp_hal_delay_ms(mp_uint_t ms) {
    // STM32: proper delay with event handling
    mp_uint_t start = mp_hal_ticks_ms();
    while (mp_hal_ticks_ms() - start < ms) {
        MICROPY_EVENT_POLL_HOOK
    }
}

int mp_hal_stdin_rx_chr(void) {
    // STM32: check multiple input sources
    for (;;) {
        if (MP_STATE_PORT(pyb_stdio_uart) != NULL && 
            uart_rx_any(MP_STATE_PORT(pyb_stdio_uart))) {
            return uart_rx_char(MP_STATE_PORT(pyb_stdio_uart));
        }
        MICROPY_EVENT_POLL_HOOK
    }
}
```

### Step 4: Main Entry Point

#### `main.c` (Application Entry)

**Purpose**: Main application loop and MicroPython initialization.

**Minimal Implementation (from minimal port)**:

```c
// Minimal port shows the absolute minimum required
int main(int argc, char **argv) {
    mp_stack_ctrl_init();
    mp_stack_set_limit(STACK_LIMIT);
    
    #if MICROPY_ENABLE_GC
    gc_init(heap, heap + sizeof(heap));
    #endif
    
    mp_init();
    
    #if MICROPY_REPL_EVENT_DRIVEN
    pyexec_event_repl_init();
    for (;;) {
        int c = mp_hal_stdin_rx_chr();
        if (pyexec_event_repl_process_char(c)) {
            break;
        }
    }
    #else
    pyexec_friendly_repl();
    #endif
    
    mp_deinit();
    return 0;
}
```

**Full Implementation (STM32 pattern)**:

```c
// STM32 main.c pattern - comprehensive initialization
int main(void) {
    // STM32 HAL init
    HAL_Init();
    
    // Configure clocks
    SystemClock_Config();
    
    // Basic hardware init
    powerctrl_check_enter_bootloader();
    
    // Board-specific initialization
    MICROPY_BOARD_EARLY_INIT();
    
    // Enable caches (STM32-specific)
    #if defined(MICROPY_BOARD_STARTUP)
    MICROPY_BOARD_STARTUP();
    #endif
    
    // Initialize systick for timing
    systick_init();
    pendsv_init();
    
    // Initialize storage
    #if MICROPY_HW_ENABLE_STORAGE
    storage_init();
    #endif
    
    // GC init with STM32's heap calculation
    #if MICROPY_ENABLE_GC
    gc_init(&_heap_start, &_heap_end);
    #endif
    
    // Initialize stack pointer for stack checking
    mp_stack_set_top(&_estack);
    mp_stack_set_limit((char*)&_estack - (char*)&_sstack - STACK_LIMIT);
    
    // Main MicroPython loop
    for (;;) {
        #if MICROPY_HW_ENABLE_STORAGE
        storage_init();
        #endif
        
        // STM32 resets peripherals on soft reset
        machine_init();
        
        // Run MicroPython
        mp_init();
        
        // STM32 runs boot.py and main.py
        #if MICROPY_VFS
        pyexec_file_if_exists("boot.py");
        pyexec_file_if_exists("main.py");
        #endif
        
        // Run REPL
        for (;;) {
            if (pyexec_mode_kind == PYEXEC_MODE_RAW_REPL) {
                if (pyexec_raw_repl() != 0) {
                    break;
                }
            } else {
                if (pyexec_friendly_repl() != 0) {
                    break;
                }
            }
        }
        
        soft_reset_exit:
        mp_printf(MP_PYTHON_PRINTER, "MPY: soft reboot\n");
        gc_sweep_all();
        mp_deinit();
    }
}

// Required MicroPython callbacks
void gc_collect(void) {
    gc_collect_start();
    gc_helper_collect_regs_and_stack();
    gc_collect_end();
}

void nlr_jump_fail(void *val) {
    mp_printf(&mp_plat_print, "FATAL: uncaught exception %p\n", val);
    mp_obj_print_exception(&mp_plat_print, MP_OBJ_FROM_PTR(val));
    for (;;) {
        __WFE();
    }
}
```

### Step 5: Build System

#### A. `Makefile` (Build Configuration)

**Purpose**: Defines how to build the port.

**Common Pattern Analysis**:
- Board selection: `BOARD ?= DEFAULT_BOARD`  
- Include core makefiles: `include ../../py/mkenv.mk`
- Cross-compiler: `CROSS_COMPILE ?= arm-none-eabi-`
- Git submodules for dependencies

**Build System Architecture Choices**:

1. **Pure Make** (STM32, SAMD, NRF, minimal)
   - Traditional approach for bare-metal ports
   - Direct control over build process
   - No external build system dependencies

2. **Make wrapping CMake** (ESP32, RP2)
   - Required when vendor SDKs mandate CMake
   - Make provides consistent user interface
   - CMake handles vendor-specific complexity
   
   **ESP32 Example**:
   ```makefile
   # Makefile for MicroPython on ESP32.
   # This is a simple, convenience wrapper around idf.py (which uses cmake).
   
   all:
       $(Q)idf.py $(IDFPY_FLAGS) -B $(BUILD) build
   ```
   
   **RP2 Example**:
   ```makefile
   # Makefile for micropython on Raspberry Pi RP2
   # This is a simple wrapper around cmake
   
   all:
       $(Q)[ -e $(BUILD)/Makefile ] || cmake -S . -B $(BUILD) -DPICO_BUILD_DOCS=0 ${CMAKE_ARGS}
       $(Q)$(MAKE) $(MAKE_ARGS) -C $(BUILD)
   ```

**Key Insight**: The Make wrapper pattern allows MicroPython to maintain a consistent `make` interface across all ports while accommodating vendor requirements. Users always run `make BOARD=xxx` regardless of underlying build system.

**Minimal Makefile (from minimal port)**:
```makefile
# Minimal port Makefile - simplest possible build
include ../../py/mkenv.mk

# qstr definitions (minimal port keeps it simple)
QSTR_DEFS = qstrdefsport.h

# include py core make definitions
include $(TOP)/py/py.mk
include $(TOP)/extmod/extmod.mk

CROSS_COMPILE ?= arm-none-eabi-

INC += -I.
INC += -I$(TOP)
INC += -I$(BUILD)

SRC_C = \
	main.c \
	uart_core.c \
	mphalport.c

OBJ = $(PY_O) $(addprefix $(BUILD)/, $(SRC_C:.c=.o))

all: $(BUILD)/firmware.elf

$(BUILD)/firmware.elf: $(OBJ)
	$(ECHO) "LINK $@"
	$(Q)$(LD) $(LDFLAGS) -o $@ $^ $(LIBS)
	$(Q)$(SIZE) $@

include $(TOP)/py/mkrules.mk
```

**Full-Featured Makefile (STM32 pattern)**:
```makefile
# STM32 Makefile pattern - comprehensive build system
BOARD ?= PYBV10
BOARD_DIR ?= boards/$(BOARD)

# If the build directory is not given, make it reflect the board name.
BUILD ?= build-$(BOARD)

include ../../py/mkenv.mk
-include mpconfigport.mk
include $(BOARD_DIR)/mpconfigboard.mk

# Configure for STM32 MCU family
CMSIS_MCU_LOWER = $(shell echo $(CMSIS_MCU) | tr '[:upper:]' '[:lower:]')
STARTUP_FILE ?= lib/stm32lib/CMSIS/STM32$(MCU_SERIES_UPPER)xx/Source/Templates/gcc/startup_$(CMSIS_MCU_LOWER).s

# Select the cross compile prefix
CROSS_COMPILE ?= arm-none-eabi-

INC += -I.
INC += -I$(TOP)
INC += -I$(BUILD)
INC += -I$(BOARD_DIR)
INC += -Ilwip_inc

# Basic source files
SRC_C = \
	main.c \
	system_stm32.c \
	stm32_it.c \
	mphalport.c \

SRC_O = \
	$(STARTUP_FILE) \
	gchelper.o \

# Add STM32 HAL drivers
SRC_STM32 = \
	$(addprefix $(STM32LIB_HAL_BASE)/Src/stm32$(MCU_SERIES)xx_,\
		hal.c \
		hal_cortex.c \
		hal_dma.c \
		hal_gpio.c \
		hal_rcc.c \
	)

OBJ = $(PY_O)
OBJ += $(addprefix $(BUILD)/, $(SRC_C:.c=.o))
OBJ += $(addprefix $(BUILD)/, $(SRC_O))
OBJ += $(addprefix $(BUILD)/, $(SRC_STM32:.c=.o))

include $(TOP)/py/py.mk
```

### Step 6: Board Configuration

#### A. `boards/YOUR_BOARD/mpconfigboard.h`

**Purpose**: Board-specific hardware definitions.

```c
// Minimal board configuration (from minimal port)
#define MICROPY_HW_BOARD_NAME "minimal"
#define MICROPY_HW_MCU_NAME   "Cortex-M4"

// STM32 board configuration pattern (from PYBV10)
#define MICROPY_HW_BOARD_NAME       "PYBv1.0"
#define MICROPY_HW_MCU_NAME         "STM32F405RG"

// Crystal frequencies
#define MICROPY_HW_CLK_PLLM (12)
#define MICROPY_HW_CLK_PLLN (336)
#define MICROPY_HW_CLK_PLLP (2)
#define MICROPY_HW_CLK_PLLQ (7)

// UART config for REPL
#define MICROPY_HW_UART_REPL        PYB_UART_1
#define MICROPY_HW_UART_REPL_BAUD   115200

// Hardware features
#define MICROPY_HW_HAS_SWITCH       (1)
#define MICROPY_HW_HAS_FLASH        (1)
#define MICROPY_HW_HAS_SDCARD       (1)
#define MICROPY_HW_HAS_LCD          (1)
#define MICROPY_HW_ENABLE_RNG       (1)
#define MICROPY_HW_ENABLE_RTC       (1)
#define MICROPY_HW_ENABLE_DAC       (1)
#define MICROPY_HW_ENABLE_USB       (1)

// Flash configuration  
#define MICROPY_HW_FLASH_SIZE_MB    (2)

// Enable features for this board
#define MICROPY_HW_ENABLE_USB       (1)
#define MICROPY_HW_ENABLE_SDCARD    (0)
```

#### B. `boards/YOUR_BOARD/mpconfigboard.mk`

**Purpose**: Board-specific build settings.

```makefile
MCU_SERIES = your_mcu_series
CMSIS_MCU = YOUR_MCU_DEFINE
STARTUP_FILE = lib/your_sdk/startup_your_mcu.s

# Linker script
LD_FILES = mcu/your_mcu.ld
```

---

## Phase 2: System Services

### Step 7: Interrupt and Timing System

#### A. `irq.h` (Interrupt Priorities)

**Purpose**: Define interrupt priority levels.

**STM32 Pattern** (`ports/stm32/irq.h`):
```c
// STM32 uses NVIC priority grouping with 4 bits for preemption
// Higher number = lower priority
#define IRQ_PRI_SYSTICK         NVIC_EncodePriority(NVIC_PRIORITYGROUP_4, 8, 0)
#define IRQ_PRI_UART            NVIC_EncodePriority(NVIC_PRIORITYGROUP_4, 12, 0)
#define IRQ_PRI_FLASH           NVIC_EncodePriority(NVIC_PRIORITYGROUP_4, 12, 0)
#define IRQ_PRI_USB             NVIC_EncodePriority(NVIC_PRIORITYGROUP_4, 14, 0)
#define IRQ_PRI_PENDSV          NVIC_EncodePriority(NVIC_PRIORITYGROUP_4, 15, 0)

// For simpler MCUs, use raw priority values
#define IRQ_PRI_SYSTICK     (0x40)  // Highest priority  
#define IRQ_PRI_UART        (0x80)
#define IRQ_PRI_PENDSV      (0xc0)  // Lowest priority
```

#### B. `pendsv.c` & `pendsv.h` (PendSV Handler)

**Purpose**: Handle deferred processing (background tasks).

**Pattern**: Used by networking, Bluetooth, and other async operations.

### Step 8: Memory Management

#### A. Linker Script (`mcu/your_mcu.ld`)

**Purpose**: Define memory layout for the target MCU.

```ld
MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 2048K
    RAM (rwx)   : ORIGIN = 0x20000000, LENGTH = 512K
}

/* Stack at top of RAM */
__StackTop = ORIGIN(RAM) + LENGTH(RAM);
__StackLimit = __StackTop - 64K;

/* Heap for MicroPython GC */
__GcHeapStart = _end;
__GcHeapEnd = __StackLimit;
```

---

## Phase 3: Basic Machine Module

### Step 9: Machine Module Foundation

#### A. `modmachine.c` (Machine Module)

**Purpose**: Implements the `machine` module.

**STM32 Implementation Pattern**:

```c
// STM32's modmachine.c - demonstrates the include file pattern
#include "py/runtime.h"
#include "extmod/modmachine.h"
#include "drivers/dht/dht.h"

#if MICROPY_PY_MACHINE

// STM32 resets via NVIC
static mp_obj_t machine_reset(void) {
    NVIC_SystemReset();
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_0(machine_reset_obj, machine_reset);

// STM32 uses HAL to get unique ID  
static mp_obj_t machine_unique_id(void) {
    byte *id = (byte *)MP_HAL_UNIQUE_ID_ADDRESS;
    return mp_obj_new_bytes(id, 12);
}
MP_DEFINE_CONST_FUN_OBJ_0(machine_unique_id_obj, machine_unique_id);

// STM32 freq functions
static mp_obj_t machine_freq(size_t n_args, const mp_obj_t *args) {
    if (n_args == 0) {
        // Get frequency
        return mp_obj_new_int(HAL_RCC_GetSysClockFreq());
    } else {
        // Set frequency (STM32 specific)
        mp_int_t freq = mp_obj_get_int(args[0]);
        if (!set_sys_clock_source(freq)) {
            mp_raise_ValueError(MP_ERROR_TEXT("invalid freq"));
        }
        return mp_const_none;
    }
}
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(machine_freq_obj, 0, 1, machine_freq);

// The actual module uses MICROPY_PY_MACHINE_INCLUDEFILE
// This allows extmod/modmachine.c to handle the standard parts
// while the port adds its own specifics in modmachine.c
#include MICROPY_PY_MACHINE_INCLUDEFILE

#endif // MICROPY_PY_MACHINE
```

### Step 10: Pin Support

#### A. `machine_pin.c` (GPIO Implementation)

**Purpose**: Implement `machine.Pin` class for GPIO control.

**Common Pattern Analysis** (study STM32/RP2 implementations):

```c
#include "py/runtime.h"
#include "py/mphal.h"
#include "extmod/modmachine.h"

typedef struct _machine_pin_obj_t {
    mp_obj_base_t base;
    qstr name;
    uint32_t pin_id;
    // Hardware-specific fields
    GPIO_TypeDef *gpio;
    uint32_t pin_mask;
} machine_pin_obj_t;

// Pin mapping table
const machine_pin_obj_t machine_pin_obj[] = {
    {{&machine_pin_type}, MP_QSTR_A0, 0, GPIOA, GPIO_PIN_0},
    {{&machine_pin_type}, MP_QSTR_A1, 1, GPIOA, GPIO_PIN_1},
    // ... more pins
};

static void machine_pin_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind) {
    machine_pin_obj_t *self = MP_OBJ_TO_PTR(self_in);
    mp_printf(print, "Pin(%q)", self->name);
}

mp_obj_t machine_pin_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *all_args) {
    enum { ARG_id, ARG_mode, ARG_pull, ARG_value };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_id, MP_ARG_REQUIRED | MP_ARG_OBJ },
        { MP_QSTR_mode, MP_ARG_INT, {.u_int = GPIO_MODE_INPUT} },
        { MP_QSTR_pull, MP_ARG_OBJ, {.u_rom_obj = MP_ROM_NONE} },
        { MP_QSTR_value, MP_ARG_KW_ONLY | MP_ARG_OBJ, {.u_rom_obj = MP_ROM_NONE} },
    };

    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all_kw_array(n_args, n_kw, all_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    // Get pin object
    machine_pin_obj_t *pin = pin_find(args[ARG_id].u_obj);
    
    // Configure pin
    if (args[ARG_mode].u_int != GPIO_MODE_INPUT) {
        machine_pin_config(pin, args[ARG_mode].u_int, args[ARG_pull].u_obj);
    }
    
    return MP_OBJ_FROM_PTR(pin);
}

// Pin methods: value(), init(), etc.
static mp_obj_t machine_pin_value(size_t n_args, const mp_obj_t *args) {
    machine_pin_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    if (n_args == 1) {
        // Get value
        return MP_OBJ_NEW_SMALL_INT(HAL_GPIO_ReadPin(self->gpio, self->pin_mask));
    } else {
        // Set value  
        HAL_GPIO_WritePin(self->gpio, self->pin_mask, mp_obj_is_true(args[1]));
        return mp_const_none;
    }
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(machine_pin_value_obj, 1, 2, machine_pin_value);

static const mp_rom_map_elem_t machine_pin_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_value), MP_ROM_PTR(&machine_pin_value_obj) },
    // ... more methods
};
static MP_DEFINE_CONST_DICT(machine_pin_locals_dict, machine_pin_locals_dict_table);

MP_DEFINE_CONST_OBJ_TYPE(
    machine_pin_type,
    MP_QSTR_Pin,
    MP_TYPE_FLAG_NONE,
    make_new, machine_pin_make_new,
    print, machine_pin_print,
    locals_dict, &machine_pin_locals_dict
);
```

---

## Phase 4: Storage and Filesystem

### Step 11: Flash Storage

**Purpose**: Implement storage backend for filesystem.

**STM32 Storage Pattern**:

STM32 implements storage through `storage.c` and `flashbdev.c`:

```c
// STM32 storage.c pattern
static const mp_obj_base_t pyb_flash_obj = {&pyb_flash_type};

// STM32 defines a block device interface
static mp_obj_t pyb_flash_readblocks(mp_obj_t self, mp_obj_t block_num, mp_obj_t buf) {
    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(buf, &bufinfo, MP_BUFFER_WRITE);
    FLASH_read_blocks(bufinfo.buf, mp_obj_get_int(block_num), bufinfo.len / FLASH_BLOCK_SIZE);
    return mp_const_none;
}

// Register with VFS
MP_DEFINE_CONST_FUN_OBJ_3(pyb_flash_readblocks_obj, pyb_flash_readblocks);
```

**Key Points**:
- Implement block device protocol (readblocks, writeblocks, ioctl)
- Handle flash programming constraints (erase before write)
- Register with VFS for filesystem support

### Step 12: USB MSC Support

**Purpose**: Expose filesystem over USB Mass Storage.

**Dependencies**: TinyUSB integration (see `usbd.c`, `msc_disk.c`)

---

## Phase 5: Peripheral Support

### Step 13: Adding Peripheral Classes

For each peripheral (UART, I2C, SPI, ADC, etc.), follow this pattern:

#### A. Update Build System

1. **Add source file to Makefile**:
```makefile
SRC_C += machine_i2c.c
```

2. **Add hardware driver** (if needed):
```makefile  
# STM32 adds HAL drivers
SRC_STM32 += $(STM32LIB_HAL_BASE)/Src/stm32$(MCU_SERIES)xx_hal_i2c.c
```

#### B. Enable in Configuration

**In `mpconfigport.h`**:
```c
#define MICROPY_PY_MACHINE_I2C                  (MICROPY_HW_ENABLE_HW_I2C)
#define MICROPY_PY_MACHINE_I2C_TRANSFER_WRITE1  (1)
```

#### C. Implement Peripheral Class

**STM32 Peripheral Pattern** (I2C example):

1. **Define object structure** (from STM32):
```c
typedef struct _machine_i2c_obj_t {
    mp_obj_base_t base;
    I2C_HandleTypeDef *i2c;  // STM32 HAL handle
    bool is_initialised;
    uint8_t scl;
    uint8_t sda;
} machine_i2c_obj_t;
```

2. **Create instance table** (STM32 pattern):
```c
// STM32 uses a macro to define I2C objects
#define I2C_OBJ(n) &machine_i2c_obj[n]
static machine_i2c_obj_t machine_i2c_obj[] = {
    #if defined(MICROPY_HW_I2C0_SCL)
    [0] = {{&machine_i2c_type}, 0, (I2C_Type *)I2C0_BASE, MICROPY_HW_I2C0_SCL, MICROPY_HW_I2C0_SDA},
    #endif
    // ... more instances
};
```

3. **Implement standard methods**:
- `make_new()` - Object construction and hardware initialization
- `print()` - String representation  
- Protocol methods (e.g., `transfer()` for I2C)

4. **Register with machine module**:
```c
{ MP_ROM_QSTR(MP_QSTR_I2C), MP_ROM_PTR(&machine_i2c_type) },
```

---

## Phase 6: Advanced Features

### Step 14: Networking Support

If your hardware supports networking:

1. **Enable in configuration**:
```c
#define MICROPY_PY_NETWORK              (1)
#define MICROPY_PY_SOCKET               (1)
```

2. **Implement network interface** in `mpnetworkport.c`

3. **Add LWIP integration** (if using LWIP stack)

### Step 15: Bluetooth Support

For Bluetooth-enabled hardware:

1. **Choose Bluetooth stack** (BTstack, NimBLE)
2. **Implement HCI transport** in `mpbthciport.c`  
3. **Enable in configuration**:
```c
#define MICROPY_PY_BLUETOOTH            (1)
```

### Step 16: Multi-core Support

For multi-core MCUs (RP2 has dual-core support):

1. **Implement Open-AMP backend** (`mpmetalport.c`, `mpremoteprocport.c`)
2. **Add core-specific configurations**
3. **Handle inter-core communication**

---

## Phase 7: Testing and Validation

### Step 17: Testing Strategy

1. **Unit Tests**: Run MicroPython test suite
```bash
cd ports/unix
make test_full
```

2. **Hardware-in-Loop**: Test on actual hardware
```bash
cd ports/yourport  
make BOARD=YOUR_BOARD
# Flash and test on hardware
```

3. **Peripheral Tests**: Create hardware-specific test scripts

### Step 18: Documentation

1. **README.md**: Build instructions, supported features
2. **Board documentation**: Pin assignments, jumper settings  
3. **API documentation**: Port-specific extensions

---

## Common Pitfalls and Best Practices

### Build System Choice
- **Start with pure Make** unless vendor SDK requires otherwise
- **Use Make wrappers** when vendor tools (ESP-IDF, Pico SDK) mandate CMake
- **Document build dependencies** clearly in README
- **Maintain consistent user interface** - always support `make BOARD=xxx`

### Vendor SDK Integration
- **Document all external dependencies** clearly
- **Provide simplified build options** where possible  
- **Don't require vendor IDEs** for basic builds
- **Version lock vendor dependencies** to ensure reproducibility

When vendor SDKs require CMake:
- ESP32: ESP-IDF uses CMake internally via `idf.py`
- RP2: Pico SDK is CMake-based
- Solution: Wrap vendor tools with Make for consistency

### Memory Management
- **Always define proper memory regions** in linker script
- **Test with different heap sizes** - GC pressure reveals bugs
- **Use `MP_REGISTER_ROOT_POINTER`** for global objects

### Interrupt Handling  
- **Keep ISRs minimal** - defer work to PendSV/main loop
- **Use proper priorities** - timing-critical > user code > background tasks
- **Test interrupt nesting** scenarios

### Hardware Integration
- **Follow existing peripheral patterns** - don't reinvent APIs
- **Handle hardware quirks gracefully** (see STM32 DMA constraints, RP2 PIO limitations)
- **Add proper error handling** and timeouts

### Build System
- **Use consistent naming** for boards and configurations
- **Minimize external dependencies** - prefer git submodules
- **Support both debug and release builds**

### Pin Configuration
- **Create comprehensive pin mapping** in `pins.csv`  
- **Support alternate functions** for peripherals
- **Handle pin conflicts** (multiple peripherals on same pins)

---

## Maintenance and Evolution

### Keeping Up with MicroPython
- **Monitor MicroPython releases** for API changes
- **Participate in community** discussions
- **Contribute improvements** back to mainline

### Adding New Features  
- **Follow established patterns** from other ports
- **Add comprehensive tests** for new functionality
- **Document changes** thoroughly

### Performance Optimization
- **Profile with real workloads** 
- **Optimize critical paths** (GC, interrupt handling)
- **Consider hardware-specific optimizations** (DMA, etc.)

---

This guide provides a comprehensive roadmap for developing a new MicroPython port. The key is to start with a minimal working foundation and incrementally add features, following the patterns established by existing successful ports.