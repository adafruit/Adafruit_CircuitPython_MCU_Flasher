# SPDX-FileCopyrightText: Copyright (c) 2023 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
"""

from . import sam

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MCU_Flasher.git"

class SAMx5(sam.SAM):
    def select(self):
        self.reset_with_extension()

        device_id = self.read_word(DAP_DSU_DID)
        if device_id not in SAMD_DEVICES:
            return
        print("device_id", hex(device_id))

        locked = self.read_word(DAP_DSU_CTRL_STATUS) & 0x00010000;
        if locked:
            print("Device is locked, must be unlocked first!")
        else:
            print("Device is unlocked")

        return None
