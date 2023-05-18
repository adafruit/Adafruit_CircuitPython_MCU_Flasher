# SPDX-FileCopyrightText: Copyright (c) 2023 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
"""

from . import DapTarget
from micropython import const

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MCU_Flasher.git"

DAP_FLASH_START = 0
DAP_FLASH_ROW_SIZE = 256
DAP_FLASH_PAGE_SIZE = 64

_DHCSR                   = const(0xe000edf0)
_DEMCR                   = const(0xe000edfc)
_AIRCR                   = const(0xe000ed0c)

_DAP_DSU_CTRL_STATUS     = const(0x41002100) # Used for accessing both CTRL, STATUSA and STATUSB from external debugger
_DAP_DSU_DID             = const(0x41002118)
_DAP_DSU_ADDR            = const(0x41002104)
_DAP_DSU_DATA            = const(0x4100210C)
_DAP_DSU_LENGTH          = const(0x41002108)

_DAP_DSU_CTRL_CRC        = const(0x00000004)
_DAP_DSU_STATUSA_DONE    = const(0x00000100)
_DAP_DSU_STATUSA_CRSTEXT = const(0x00000200)
_DAP_DSU_STATUSA_BERR    = const(0x00000400)

_NVMCTRL_CTRLA           = const(0x41004000)
_NVMCTRL_CTRLB           = const(0x41004004)
_NVMCTRL_PARAM           = const(0x41004008)
_NVMCTRL_INTFLAG         = const(0x41004014)
_NVMCTRL_STATUS          = const(0x41004018)
_NVMCTRL_ADDR            = const(0x4100401c)

_USER_ROW_ADDR           = const(0x00804000)

_NVMCTRL_CMD_ER          = const(0xa502)
_NVMCTRL_CMD_WP          = const(0xa504)
_NVMCTRL_CMD_EAR         = const(0xa505)
_NVMCTRL_CMD_WAP         = const(0xa506)
_NVMCTRL_CMD_WL          = const(0xa50f)
_NVMCTRL_CMD_UR          = const(0xa541)
_NVMCTRL_CMD_PBC         = const(0xa544)
_NVMCTRL_CMD_SSB         = const(0xa545)


SAMD_DEVICES = {
#   Device ID    Name           Flash size        Erase size
    0x10040100: ("SAM D09D14A", 16 * 1024, 256),
    0x10040107: ("SAM D09C13A", 8 * 1024, 128),
    0x10020100: ("SAM D10D14AM", 16 * 1024, 256),
    0x10030100: ("SAM D11D14A", 16 * 1024, 256),
    0x10030000: ("SAM D11D14AM", 16 * 1024, 256),
    0x10030003: ("SAM D11D14AS", 16 * 1024, 256),
    0x10030103: ("SAM D11D14AS (Rev B)", 16 * 1024, 256),
    0x10030006: ("SAM D11C14A", 16 * 1024, 256),
    0x10030106: ("SAM D11C14A (Rev B)", 16 * 1024, 256),
    0x1000120d: ("SAM D20E15A", 32 * 1024, 512),
    0x1000140a: ("SAM D20E18A", 256 * 1024, 4096),
    0x10001100: ("SAM D20J18A", 256 * 1024, 4096),
    0x10001200: ("SAM D20J18A (Rev C)", 256 * 1024, 4096),
    0x10010100: ("SAM D21J18A", 256 * 1024, 4096),
    0x10010200: ("SAM D21J18A (Rev C)", 256 * 1024, 4096),
    0x10010300: ("SAM D21J18A (Rev D)", 256 * 1024, 4096),
    0x1001020d: ("SAM D21E15A (Rev C)", 32 * 1024, 512),
    0x1001030a: ("SAM D21E18A", 256 * 1024, 4096),
    0x10010205: ("SAM D21G18A", 256 * 1024, 4096),
    0x10010305: ("SAM D21G18A (Rev D)", 256 * 1024, 4096),
    0x10010019: ("SAM R21G18 ES", 256 * 1024, 4096),
    0x10010119: ("SAM R21G18", 256 * 1024, 4096),
    0x10010219: ("SAM R21G18A (Rev C)", 256 * 1024, 4096),
    0x10010319: ("SAM R21G18A (Rev D)", 256 * 1024, 4096),
    0x11010100: ("SAM C21J18A ES", 256 * 1024, 4096),
    0x10810219: ("SAM L21E18B", 256 * 1024, 4096),
    0x10810000: ("SAM L21J18A", 256 * 1024, 4096),
    0x1081010f: ("SAM L21J18B (Rev B)", 256 * 1024, 4096),
    0x1081020f: ("SAM L21J18B (Rev C)", 256 * 1024, 4096),
    0x1081021e: ("SAM R30G18A", 256 * 1024, 4096),
    0x1081021f: ("SAM R30E18A", 256 * 1024, 4096),
}
class SAM(DapTarget):
    def reset_with_extension(self):
        # bring the CPU out of reset while holding swclk low
        self.probe.write_pins(PROTOCOL_PINS, 0x11, 0x00)
        self.probe.write_pins(PROTOCOL_PINS, 0x11, 0x10)
        self.probe.write_pins(PROTOCOL_PINS, 0x11, 0x11)
        self.target_connect()
        self.target_prepare()

    def finish_reset(self):
        # Stop the core
        self.write_word(DHCSR, 0xa05f0003);
        self.write_word(DEMCR, 0x00000001);
        self.write_word(AIRCR, 0x05fa0004);

        # Release the reset
        self.write_word(DAP_DSU_CTRL_STATUS, DAP_DSU_STATUSA_CRSTEXT);

    def select(self) -> Optional[int]:
        self.reset_with_extension()

        device_id = self.read_word(DAP_DSU_DID)
        print("device_id", hex(device_id))


        if device_id not in SAMD_DEVICES:
            return
        self.device = SAMD_DEVICES[device_id]
        print("device", self.device[0])

        locked = self.read_word(DAP_DSU_CTRL_STATUS) & 0x00010000;
        if locked:
            print("Device is locked, must be unlocked first!")
        else:
            print("Device is unlocked")

        self.finish_reset() 
