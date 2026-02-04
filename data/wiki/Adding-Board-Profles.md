# Adding New Board Profiles to MicroPython

This guide explains how to add support for a new board to MicroPython. The process varies depending on whether your CPU/MCU is already supported or requires new support.

## Overview

MicroPython is organized into **ports** (platform-specific implementations) that contain **boards** (specific hardware configurations). Each port supports multiple related CPU families:

- **stm32**: STM32 microcontrollers (F0, F4, F7, G0, G4, H5, H7, L0, L1, L4, WB, WL series)
- **esp32**: ESP32 family chips
- **rp2**: Raspberry Pi Pico (RP2040/RP2350)
- **samd**: Microchip SAMD21/SAMD51 microcontrollers
- **mimxrt**: NXP i.MX RT series
- **renesas-ra**: Renesas RA series
- **nrf**: Nordic nRF series
- And others...

## Quick Start: Adding a Board with Existing CPU Support

If your board uses a CPU/MCU that's already supported by MicroPython, follow these steps:

### 1. Identify the Correct Port

Determine which port your board belongs to based on the CPU/MCU:

```bash
# Check existing boards for your CPU family
ls ports/stm32/boards/    # For STM32 boards
ls ports/esp32/boards/    # For ESP32 boards
ls ports/rp2/boards/      # For RP2040/RP2350 boards
ls ports/samd/boards/     # For SAMD21/SAMD51 boards
```

### 2. Find a Similar Board

Look for a board that uses the same or similar MCU as your target board:

```bash
# For STM32, check MCU series in existing boards
grep -h "MCU_SERIES" ports/stm32/boards/*/mpconfigboard.mk | sort | uniq
grep -h "CMSIS_MCU" ports/stm32/boards/*/mpconfigboard.mk | sort | uniq
```

### 3. Create the Board Directory

Create a new directory for your board:

```bash
cd ports/[PORT]/boards/
mkdir YOUR_BOARD_NAME
cd YOUR_BOARD_NAME
```

Use naming conventions:
- **STM32**: `VENDOR_MODEL` (e.g., `NUCLEO_F401RE`, `ARDUINO_GIGA`)
- **ESP32**: `VENDOR_MODEL_ESP32` (e.g., `SPARKFUN_IOT_REDBOARD_ESP32`)
- **RP2**: `VENDOR_MODEL` (e.g., `RPI_PICO`, `ADAFRUIT_FEATHER_RP2040`)

### 4. Create Required Files

Each board requires specific files depending on the port:

#### STM32 Boards (Minimum Required Files)

**`mpconfigboard.h`** - Hardware configuration:
```c
#define MICROPY_HW_BOARD_NAME       "Your Board Name"
#define MICROPY_HW_MCU_NAME         "STM32F401xE"

#define MICROPY_HW_HAS_SWITCH       (1)
#define MICROPY_HW_HAS_FLASH        (1)
#define MICROPY_HW_ENABLE_RTC       (1)

// Clock configuration
#define MICROPY_HW_CLK_USE_HSI      (1)
#define MICROPY_HW_CLK_PLLM         (16)
#define MICROPY_HW_CLK_PLLN         (336)
#define MICROPY_HW_CLK_PLLP         (RCC_PLLP_DIV4)
#define MICROPY_HW_CLK_PLLQ         (7)

// UART config
#define MICROPY_HW_UART2_TX         (pin_A2)
#define MICROPY_HW_UART2_RX         (pin_A3)
#define MICROPY_HW_UART_REPL        PYB_UART_2
#define MICROPY_HW_UART_REPL_BAUD   115200

// I2C buses
#define MICROPY_HW_I2C1_SCL         (pin_B8)
#define MICROPY_HW_I2C1_SDA         (pin_B9)

// SPI buses
#define MICROPY_HW_SPI1_NSS         (pin_A15)
#define MICROPY_HW_SPI1_SCK         (pin_A5)
#define MICROPY_HW_SPI1_MISO        (pin_A6)
#define MICROPY_HW_SPI1_MOSI        (pin_A7)

// User switch
#define MICROPY_HW_USRSW_PIN        (pin_C13)
#define MICROPY_HW_USRSW_PULL       (GPIO_NOPULL)
#define MICROPY_HW_USRSW_EXTI_MODE  (GPIO_MODE_IT_FALLING)
#define MICROPY_HW_USRSW_PRESSED    (0)

// LEDs
#define MICROPY_HW_LED1             (pin_A5)
#define MICROPY_HW_LED_ON(pin)      (mp_hal_pin_high(pin))
#define MICROPY_HW_LED_OFF(pin)     (mp_hal_pin_low(pin))
```

**`mpconfigboard.mk`** - Build configuration:
```makefile
MCU_SERIES = f4
CMSIS_MCU = STM32F401xE
AF_FILE = boards/stm32f401_af.csv
LD_FILES = boards/stm32f401xe.ld boards/common_ifs.ld
TEXT0_ADDR = 0x08000000
TEXT1_ADDR = 0x08020000
```

**`pins.csv`** - Pin mapping:
```
D0,PA3
D1,PA2
D2,PA10
# ... more pin mappings
LED_GREEN,PA5
SW,PC13
```

**`board.json`** - Board metadata:
```json
{
    "deploy": [
        "../deploy.md"
    ],
    "docs": "",
    "features": [],
    "images": [
        "your_board.jpg"
    ],
    "mcu": "stm32f4",
    "product": "Your Board Name",
    "thumbnail": "",
    "url": "https://vendor.com/your-board",
    "vendor": "Your Vendor"
}
```

**`stm32f4xx_hal_conf.h`** - HAL configuration (copy from similar board and modify if needed)

#### ESP32 Boards

**`mpconfigboard.h`**:
```c
#define MICROPY_HW_BOARD_NAME "Your ESP32 Board"
#define MICROPY_HW_MCU_NAME "ESP32"

#define MICROPY_HW_ENABLE_SDCARD    (1)
#define MICROPY_HW_ENABLE_MDNS      (1)
// ... other features
```

**`mpconfigboard.cmake`**:
```cmake
set(IDF_TARGET esp32)
set(SDKCONFIG_DEFAULTS
    boards/sdkconfig.base
    boards/sdkconfig.ble
)
```

**`pins.csv`** and **`board.json`** similar to STM32

#### RP2 Boards

**`mpconfigboard.h`**:
```c
#define MICROPY_HW_BOARD_NAME "Your RP2 Board"
#define MICROPY_HW_FLASH_STORAGE_BYTES (1408 * 1024)
```

**`mpconfigboard.cmake`**:
```cmake
# Freeze manifest
set(MICROPY_FROZEN_MANIFEST ${CMAKE_CURRENT_LIST_DIR}/manifest.py)
```

### 5. Test the Configuration

Build and test your board configuration:

```bash
# For STM32
cd ports/stm32
make submodules  # First time only
make BOARD=YOUR_BOARD_NAME

# For ESP32
cd ports/esp32
make submodules  # First time only
make BOARD=YOUR_BOARD_NAME

# For RP2
cd ports/rp2
make submodules  # First time only
make BOARD=YOUR_BOARD_NAME
```

### 6. Additional Files (Optional)

Advanced boards may require additional files:

- **`board_init.c`** - Custom board initialization code
- **`manifest.py`** - Frozen Python modules
- **`bdev.c`** - Custom block device configuration
- **Custom linker scripts** - For non-standard memory layouts
- **`deploy.md`** - Board-specific deployment instructions

## Adding Support for New CPU Variants

If your CPU/MCU isn't supported, you'll need to add MCU support first, then create the board profile.

### Complexity Levels

**Level 1: Same family, different variant** (e.g., STM32F401 when F405 exists)
- Add new `_af.csv` file for pin definitions
- Add new linker script if memory layout differs
- Minimal port changes needed

**Level 2: New subfamily** (e.g., STM32G4 when only F4/F7 exist)
- Add new MCU series support in port
- New HAL configuration files
- Potential driver updates needed

**Level 3: Completely new CPU family**
- May require new port entirely
- Significant development effort
- Consider contributing upstream first

### Steps for New CPU Support

#### 1. Gather MCU Information

Collect essential information about your MCU:
- Pin-out and alternate function mappings
- Memory layout (Flash/RAM sizes and addresses)
- Peripheral addresses and capabilities
- Clock tree and PLL configuration options
- Power management features

#### 2. Add MCU Definition Files

For STM32 example (adding new STM32F4xx variant):

**Add AF (Alternate Function) file** - `boards/stm32f4xx_af.csv`:
```csv
Port,Pin,AF0,AF1,AF2,AF3,AF4,AF5,AF6,AF7,AF8,AF9,AF10,AF11,AF12,AF13,AF14,AF15,ADC
PortA,PA0,,TIM2_CH1/TIM2_ETR,TIM5_CH1,,,,,USART2_CTS,,,,,,,EVENTOUT,ADC1_IN0
# ... continue for all pins
```

**Add linker script** - `boards/stm32f4xxXX.ld`:
```ld
MEMORY
{
    FLASH (rx)      : ORIGIN = 0x08000000, LENGTH = 512K
    FLASH_ISR (rx)  : ORIGIN = 0x08000000, LENGTH = 16K
    FLASH_FS (rx)   : ORIGIN = 0x08004000, LENGTH = 112K
    FLASH_TEXT (rx) : ORIGIN = 0x08020000, LENGTH = 384K
    RAM (xrw)       : ORIGIN = 0x20000000, LENGTH = 96K
}
/* Include common sections */
INCLUDE "boards/common_basic.ld"
```

**Add HAL configuration** - `boards/stm32f4xx_hal_conf_base.h`:
```c
/* STM32F4xx HAL configuration template */
#include "boards/stm32f4xx_hal_conf_base.h"

/* MCU-specific overrides */
#define HAL_MODULE_ENABLED
/* ... other configuration */
```

#### 3. Update Port Configuration

Add MCU support to the port's build system:

**Update port Makefile** (`ports/stm32/Makefile`):
- Add new MCU series detection
- Add new linker script handling
- Update HAL library includes

**Update port sources** as needed:
- Clock configuration in `system_stm32.c`
- Peripheral drivers in relevant `*.c` files
- Pin definitions in `pin_defs_stm32.c`

#### 4. Add MCU Series Support

For completely new series, update:

- `mpconfigport.h` - Add MCU family detection
- HAL integration files
- Peripheral driver mappings
- Clock and power management

### Example: Adding STM32H5 Support

When STM32H5 was added to MicroPython, these changes were made:

1. **New board definition** (ports/stm32/boards/NUCLEO_H563ZI/):
   - `mpconfigboard.h` - H5-specific configuration
   - `mpconfigboard.mk` - MCU_SERIES = h5
   - `stm32h5xx_hal_conf.h` - H5 HAL config
   - `pins.csv` - H563ZI pin mapping
   - `board.json` - Metadata

2. **Port updates**:
   - Added H5 peripheral support across multiple drivers
   - Updated clock configuration for H5 MCUs
   - Added H5-specific linker scripts and memory layouts

## Pin Mapping Guidelines

The `pins.csv` file maps logical pin names to physical MCU pins:

```csv
# Format: LOGICAL_NAME,MCU_PIN
D0,PA3          # Digital pin 0 -> MCU pin PA3
A0,PA0          # Analog pin 0 -> MCU pin PA0
LED_GREEN,PA5   # Green LED -> MCU pin PA5
SW,PC13         # User switch -> MCU pin PC13
I2C1_SCL,PB8    # I2C1 clock -> MCU pin PB8
```

**Best practices:**
- Follow Arduino-style naming for maker boards (D0-D13, A0-A5)
- Use descriptive names for specialized pins (LED_RED, UART_TX)
- Include all accessible pins, even if not connected on the board
- Group related pins together (all UART pins, all SPI pins, etc.)

## Testing Your Board

### 1. Build Test

```bash
cd ports/[PORT]
make BOARD=YOUR_BOARD_NAME V=1  # Verbose output for debugging
```

### 2. Basic Functionality Test

If you have hardware, test basic features:

```python
# Test LED
import machine
led = machine.Pin("LED_GREEN", machine.Pin.OUT)
led.on()
led.off()

# Test pin access
pin = machine.Pin("D0", machine.Pin.IN)
print(pin.value())

# Test peripherals
i2c = machine.I2C(1)
print(i2c.scan())
```

### 3. Run Test Suite

```bash
# After building successfully, run tests
make test_full BOARD=YOUR_BOARD_NAME
```

## Contributing Your Board

### 1. Code Quality

- Follow MicroPython coding conventions
- Use `tools/codeformat.py` for C code formatting
- Use `ruff format` for Python code

### 2. Documentation

- Add board documentation to `docs/` if creating new port
- Update pinout documentation with pin mappings
- Include deployment instructions in `deploy.md`

### 3. Git Commit Guidelines

Commit format for board additions:
```
[port]/boards: Add [Board Name] support.

Add support for [Board Name] by [Vendor].
- [Feature 1]
- [Feature 2]
- [Feature 3]

Signed-off-by: Your Name <your.email@example.com>
```

Example:
```
stm32/boards: Add NUCLEO-H563ZI board definition.

Configuration:
- Clock is HSE, CPU runs at 250MHz.
- REPL on USB and UART connected to the ST-Link interface.
- Storage is configured for internal flash memory.
- Three LEDs and one user button.
- Ethernet is enabled.

Signed-off-by: Your Name <your.email@example.com>
```

### 4. Pull Request Process

1. **Fork** the MicroPython repository
2. **Create branch** for your board addition
3. **Commit** with sign-off (`git commit -s`)
4. **Test** thoroughly on hardware if available
5. **Submit PR** to https://github.com/micropython/micropython

**PR Template:**
```markdown
### Summary
Add support for [Board Name] by [Vendor]. This board features [key specs] and is actively sold by [vendor].

### Testing
- [x] Builds successfully
- [x] Basic pin access works
- [x] UART/I2C/SPI peripherals functional
- [ ] Not tested on hardware (specify why)

### Trade-offs and Alternatives
None - this is a simple board addition using existing MCU support.
```

## Common Issues and Solutions

### Build Errors

**"MCU not supported"**
- Check `MCU_SERIES` in `mpconfigboard.mk`
- Verify MCU family is supported by the port
- Add MCU support if needed (see Appendix)

**"Linker script not found"**
- Check `LD_FILES` path in `mpconfigboard.mk`
- Verify linker script exists in `boards/` directory
- Copy from similar MCU if needed

**"Pin not found"**
- Verify pin names in `pins.csv` match MCU datasheet
- Check pin is defined in port's pin definition files
- Ensure pin exists on the MCU package you're using

### Pin Mapping Issues

**"Pin already in use"**
- Each physical pin can only have one primary assignment
- Use alternate function mappings for multiple protocols
- Check for conflicts in `mpconfigboard.h`

**"Peripheral not working"**
- Verify pin alternate function mappings in AF CSV file
- Check peripheral is enabled in `mpconfigboard.h`
- Ensure clock is configured for the peripheral

### MCU-Specific Issues

**Clock not stable**
- Check crystal/oscillator configuration
- Verify PLL settings match your hardware
- Consider using HSI instead of HSE for initial testing

**Flash/RAM size mismatch**
- Update linker script with correct memory sizes
- Check MCU part number matches datasheet
- Verify you're using the right variant (e.g., F401RE vs F401RB)

## Appendix: Port-Specific Details

### STM32 Port

**Supported MCU Series:** F0, F4, F7, G0, G4, H5, H7, L0, L1, L4, WB, WL

**Key files in boards/ directory:**
- `stm32fxxx_af.csv` - Alternate function mappings
- `stm32fxxx.ld` - Linker scripts for specific MCUs
- `stm32fxxx_hal_conf_base.h` - HAL configuration templates
- `common_*.ld` - Shared linker script components

**Adding new STM32 MCU:**
1. Create AF CSV file from MCU datasheet
2. Add appropriate linker script for memory layout
3. Update HAL configuration if needed
4. Test with a reference board

### ESP32 Port

**Supported chips:** ESP32, ESP32-S2, ESP32-S3, ESP32-C3, ESP32-C6

**Key configuration:**
- Uses CMake build system
- `sdkconfig.*` files for ESP-IDF configuration
- Different variants supported via CMake options

### RP2 Port

**Supported MCUs:** RP2040, RP2350

**Key features:**
- CMake-based build system
- PIO (Programmable I/O) support
- Flash filesystem by default

### SAMD Port

**Supported MCUs:** SAMD21, SAMD51

**Key considerations:**
- Limited flash/RAM on SAMD21
- Different clock configurations between SAMD21/51
- USB support varies by MCU

---

This guide should get you started with adding new board support to MicroPython. For complex cases or completely new MCU families, consider reaching out to the MicroPython community first for guidance and coordination.