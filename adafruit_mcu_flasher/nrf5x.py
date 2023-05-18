# SPDX-FileCopyrightText: Copyright (c) 2023 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
"""

import time

from . import DapTarget

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MCU_Flasher.git"

NRF5X_DHCSR = 0xe000edf0
NRF5X_DEMCR = 0xe000edfc
NRF5X_AIRCR = 0xe000ed0c

NRF5X_FICR_CODEPAGESIZE = 0x10000010 # Code memory page size
NRF5X_FICR_CODESIZE = 0x10000014     # Code size (in pages)
NRF5X_FICR_HWID = 0x10000100         # Part Code
NRF5X_FICR_CHIPVARIANT = 0x10000104  # Part Variant
NRF5X_FICR_PACKAGEID = 0x10000108    # Package Options
NRF5X_FICR_SRAM = 0x1000010C         # RAM Variant
NRF5X_FICR_FLASHSIZE = 0x10000110    # Flash Variant

NRF_NVMC_BASE = 0x4001E000
NRF_NVMC_READY = NRF_NVMC_BASE + 0x400
NRF_NVMC_CONFIG = NRF_NVMC_BASE + 0x504
NRF_NVMC_ERASEALL = NRF_NVMC_BASE + 0x50c

NRF5X_FLASH_START = 0
CHUNK_SIZE = 1024

class NRF(DapTarget):
    def select(self):
        self.target_prepare()
        
        # Stop the core
        self.write_word(NRF5X_DHCSR, 0xa05f0003)
        self.write_word(NRF5X_DEMCR, 0x00000001)
        self.write_word(NRF5X_AIRCR, 0x05fa0004)

        # Family ID
        hwid = self.read_word(NRF5X_FICR_HWID)

        # Variant ID and swap its endian
        chipvariant = self.read_word(NRF5X_FICR_CHIPVARIANT)
        variant = chipvariant.to_bytes(4, "big").decode("utf-8")
        print(f"nRF{hwid:x}_{variant}")

        codepagesize = self.read_word(NRF5X_FICR_CODEPAGESIZE)
        codesize = self.read_word(NRF5X_FICR_CODESIZE)

    def deselect(self):
        self.write_word(NRF5X_DEMCR, 0x00000000)
        self.write_word(NRF5X_AIRCR, 0x05fa0004)

    def flash_ready(self) -> bool:
        return (self.read_word(NRF_NVMC_READY) & 1) != 0

    def flash_wait_ready(self) -> bool:
        start = time.monotonic()
        while (time.monotonic() - start) < 1 and not self.flash_ready():
            pass
        return self.flash_ready()

    def erase(self):
        self.write_word(NRF_NVMC_CONFIG, 2)    # Erase Enable
        self.write_word(NRF_NVMC_ERASEALL, 1)  # Erase All

        while not self.flash_ready():
            pass

        self.write_word(NRF_NVMC_CONFIG, 0)  # Disable Erase

    def program_start(self, *, offset=0, size=0):
        return NRF5X_FLASH_START + offset

    def program_flash(self, addr, buf, do_verify=True) -> bool:
        # address must be word-aligned
        if addr & 0x03 != 0:
            return False

        self.write_word(NRF_NVMC_CONFIG, 1) # Write Enable

        offset = 0
        while offset < len(buf):
            remaining = len(buf) - offset
            if remaining >= CHUNK_SIZE:
                data = memoryview(buf)[offset:offset + CHUNK_SIZE]
            else:
                data = bytearray(CHUNK_SIZE)
                for i in range(CHUNK_SIZE):
                    if i < remaining:
                        data[i] = buf[offset+i]
                    else:
                        data[i] = 0xff

            hasdata = False
            for value in data:
                if value != 0xff:
                    hasdata = True
                    break

            if hasdata:
                self.write_block(addr + offset, data)
            else:
                print("no data", addr + offset)

            if not self.flash_wait_ready():
                # Flash timed out before being ready!
                return False

            # Optionally verify the written data
            if hasdata and do_verify:
                verify_buffer = self.read_block(addr + offset, CHUNK_SIZE)
                if verify_buffer != data:
                    return False
                del verify_buffer

            offset += len(data)


        self.write_word(NRF_NVMC_CONFIG, 0) # Write Disable

        return True

    def program_uicr(self, addr, value):
        self.write_word(NRF_NVMC_CONFIG, 1) # Write Enable
        self.write_word(addr, value);
        while not self.flash_ready():
            pass
        self.write_word(NRF_NVMC_CONFIG, 0) # Write Disable
 
