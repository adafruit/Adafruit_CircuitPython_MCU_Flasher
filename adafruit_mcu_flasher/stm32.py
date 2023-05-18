# SPDX-FileCopyrightText: Copyright (c) 2023 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
"""

from . import DapTarget

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MCU_Flasher.git"

STM_DEVICE_NAMES = {
    0x413: "STM32F405xx/07xx and STM32F415xx/17xx",
    0x419: "STM32F42xxx and STM32F43xxx",
    0x431: "STM32F411xC/E",
    0x441: "STM32F412"
}

class STM32(DapTarget):
    def select(self) -> Optional[int]:
        self.target_prepare()

        # Stop the core
        self.dap.write_word(DHCSR, 0xa05f0003)
        self.dap.write_word(DEMCR, 0x00000001)
        self.dap.write_word(AIRCR, 0x05fa0004)

        self.flash_size = (self.dap.read_word(STM32_FLASHSIZE) >> 16) * 1024

        mcuid = (self.dap.read_word(DAP_DBGMCU_IDCODE) & 0xFFF);
        if mcuid in STM_DEVICE_NAMES:
            print(STM_DEVICE_NAMES[mcuid])
            return mcuid

        return None
 
