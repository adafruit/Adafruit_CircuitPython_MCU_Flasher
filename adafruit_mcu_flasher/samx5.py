# SPDX-FileCopyrightText: Copyright (c) 2023 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
"""

from . import sam

import supervisor
import time

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MCU_Flasher.git"

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
_NVMCTRL_INTFLAG         = const(0x41004010)
_NVMCTRL_STATUS          = const(0x41004012)
_NVMCTRL_ADDR            = const(0x41004014)
_NVMCTRL_RUNLOCK         = const(0x41004018)

_NVMCTRL_CMD_EP          = const(0xa500) #  /* Erase Page */
_NVMCTRL_CMD_EB          = const(0xa501) #  /* Erase Block */
_NVMCTRL_CMD_WP          = const(0xa503) #  /* Write Page */
_NVMCTRL_CMD_WQW         = const(0xa504) # /* Write 128 bit word */
_NVMCTRL_CMD_LR          = const(0xa511) #  /* Lock Region */
_NVMCTRL_CMD_UR          = const(0xa512) #  /* Unlock Region */
_NVMCTRL_CMD_SPRM        = const(0xa513) #/* Set Power Reduction Mode */
_NVMCTRL_CMD_CPRM        = const(0xa514) #/* Clear Power Reduction Mode */
_NVMCTRL_CMD_PBC         = const(0xa515) # /* Page Buffer Clear */
_NVMCTRL_CMD_SSB         = const(0xa516) # /* Set Security Bit */
_NVMCTRL_CMD_CELCK       = const(0xa518) # /* Chip Erase Lock - DSU.CTRL.CE command is not available */
_NVMCTRL_CMD_CEULCK      = const(0xa519) # /* Chip Erase Unlock - DSU.CTRL.CE command is available */
_NVMCTRL_CMD_SBPDIS      = const(0xa51a) # /* Sets STATUS.BPDIS, Boot loader protection is off until CBPDIS is issued or next start-up sequence. Page 628 */
_NVMCTRL_CMD_CBPDIS      = const(0xa51b) # /* Clears STATUS.BPDIS, Boot loader protection is not off */

_USER_ROW_ADDR           = const(0x00804000)

SAMDx5_DEVICES = {
    0x60060000: ("SAMD51P20A", 1024 * 1024, 2048),
    0x60060300: ("SAMD51P20A", 1024 * 1024, 2048),
    0x60060001: ("SAMD51P19A", 512 * 1024, 1024),
    0x60060002: ("SAMD51N20A", 1024 * 1024, 2048),
    0x60060003: ("SAMD51N19A", 512 * 1024, 1024),
    0x60060004: ("SAMD51J20A", 1024 * 1024, 2048),
    0x60060304: ("SAMD51J20A", 1024 * 1024, 2048),
    0x60060305: ("SAMD51J19A", 512 * 1024, 1024),
    0x60060005: ("SAMD51J19A", 512 * 1024, 1024),
    0x60060006: ("SAMD51J18A", 256 * 1024, 512),
    0x60060007: ("SAMD51G19A", 512 * 1024, 1024),
    0x60060307: ("SAMD51G19A", 512 * 1024, 1024),
    0x60060008: ("SAMD51G18A", 256 * 1024, 512),
    0x61810002: ("SAME51J19A", 512 * 1024, 1024),
    0x61810302: ("SAME51J19A", 512 * 1024, 1024)
}

class SAMx5(sam.SAM):
    def target_connect(self):
        self.reset_with_extension()

    def select(self):
        self.reset_with_extension()

        device_id = self.read_word(_DAP_DSU_DID)
        print("device_id", hex(device_id))
        if device_id not in SAMDx5_DEVICES:
            return

        self.device = SAMDx5_DEVICES[device_id]
        print("device", self.device[0])

        locked = self.read_word(_DAP_DSU_CTRL_STATUS) & 0x00010000;
        if locked:
            print("Device is locked, must be unlocked first!")
        else:
            print("Device is unlocked")

        self.finish_reset()

    # erase() is the same as SAMD21

    def fuse_read(self):
        # The user row is the first 32 bytes but we twice that and back up the
        # values to the second 32 bytes if they are empty. The backup won't save
        # you from an erase that wasn't followed by a write because it is also
        # erased.
        self._user_row = self.read_block(_USER_ROW_ADDR, 64)
        erased = True
        for i in range(32):
            b = self._user_row[i]
            if b != 0xff:
                erased = False
            # print(f"{(i + 1) * 8 - 1} {b:02x} {b:08b} {i * 8}")

        backup_erased = True
        for i in range(32, 64):
            b = self._user_row[i]
            if b != 0xff:
                backup_erased = False

        # Our user row is erased!
        if erased:
            if not backup_erased:
                self._user_row[:32] = self._user_row[32:]
            else:
                # Set back to defaults stated in the data sheet and from a SAMD51.
                # This won't recover factory settings.
                self._user_row[0:8] = b"\x39\x92\x9a\xfe\x80\xff\xec\xae"
        if backup_erased:
            self._user_row[32:] = self._user_row[:32]

    def fuse_write(self):
        first_byte = self._user_row[0]
        same = True
        for b in self._user_row:
            if b != first_byte:
                same = False
                break
        if same and (first_byte == 0xff or first_byte == 0x0):
            # Entire User Row fuses should never be 0 or all 1s
            raise RuntimeError("Will never write User Row fuses as all 0s or all 1s!")

        # Turn off autoreload because we don't want to erase but not write the user row.
        supervisor.runtime.autoreload = False
        # Erase the page
        self.write_word(_NVMCTRL_CTRLA, 0x4)
        self.write_word(_NVMCTRL_ADDR, _USER_ROW_ADDR)
        self.write_word(_NVMCTRL_CTRLB, _NVMCTRL_CMD_EP)
        while (self.read_word(_NVMCTRL_INTFLAG) & 1) == 0:
            pass

        start_time = time.monotonic()
        while time.monotonic() - start_time < 1 and (self.read_word(_NVMCTRL_STATUS) & 0x10000) == 0:
            pass
        if (self.read_word(_NVMCTRL_STATUS) & 0x10000) == 0:
            raise TimeoutError("Flash not ready")

        for i in range(256 // 16):
            self.write_block(_USER_ROW_ADDR + 16 * i, memoryview(self._user_row)[16 * i:16 * (i + 1)])
            self.write_word(_NVMCTRL_CTRLB, _NVMCTRL_CMD_WQW)
            while (self.read_word(_NVMCTRL_INTFLAG) & 1) == 0:
                pass
        supervisor.runtime.autoreload = True

        # Needs to reset the MCU, for it to reread the fuses
        time.sleep(1)
        self.reset_with_extension()
        self.finish_reset()

    def reset_protection_fuses(self, reset_bootloader_protection, reset_region_locks):
        do_fuse_write = False

        self.fuse_read()

        if reset_bootloader_protection and ((self._user_row[3] >> 2) & 0x7) != 0x7:
            print("Resetting BOOTPROT... ");
            self._user_row[3] |= 0x7 << 2;
            do_fuse_write = True

        if reset_region_locks and self._user_row[9:13] != b"\xff\xff\xff\xff":
            print("Resetting NVM region LOCK... ")
            self._user_row[9:13] = b"\xff\xff\xff\xff"
            do_fuse_write = True

        if do_fuse_write:
            self.fuse_write()

    def program_start(self, offset = 0, size = 0):
        # DSU.STATUSB.PROT
        if (self.read_word(_DAP_DSU_CTRL_STATUS) & 0x00010000) != 0:
            raise RuntimeError("device is locked, perform a chip erase before programming")

        self.reset_protection_fuses(True, False)

        # Temporarily turn off bootloader protection
        self.write_word(_NVMCTRL_CTRLB, _NVMCTRL_CMD_SBPDIS)
        while (self.read_word(_NVMCTRL_INTFLAG) & 1) == 0:
            pass

        self.write_word(_NVMCTRL_CTRLA, 0x04) # Manual write

        return offset

    def program_block(self, addr, buf):
        # Even after a chip erase, unlocking flash regions still might be necessary, since region locks is not cleared by Chip Erase.
        self.write_word(_NVMCTRL_ADDR, addr)
        self.write_word(_NVMCTRL_CTRLA, _NVMCTRL_CMD_UR) # Unlock Region temporary
        while self.read_word(_NVMCTRL_INTFLAG) & 1 == 0:
            pass

        self.write_block(addr, buf)

        start_time = time.monotonic()
        while time.monotonic() - start_time < 1 and (self.read_word(_NVMCTRL_STATUS) & 0x10000) == 0:
            pass
        if (self.read_word(_NVMCTRL_STATUS) & 0x10000) == 0:
            raise TimeoutError("Flash not ready")

        self.write_word(_NVMCTRL_CTRLB, _NVMCTRL_CMD_WP) # Write page from the buffer to flash
        while self.read_word(_NVMCTRL_INTFLAG) & 1 == 0:
            pass
