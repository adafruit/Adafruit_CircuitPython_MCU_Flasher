# SPDX-FileCopyrightText: Copyright (c) 2023 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_mcu_flasher`
================================================================================

Flash another microcontroller from CircuitPython. Modeled after the Adafruit_DAP Arduino library.


* Author(s): Scott Shawcroft
"""

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MCU_Flasher.git"

class DapTarget:
    SWD_DP_R_IDCODE = 0x00
    SWD_DP_W_ABORT = 0x00
    SWD_DP_R_CTRL_STAT = 0x04
    SWD_DP_W_CTRL_STAT = 0x04 # When CTRLSEL == 0
    SWD_DP_W_WCR = 0x04       # When CTRLSEL == 1
    SWD_DP_R_RESEND = 0x08
    SWD_DP_W_SELECT = 0x08
    SWD_DP_R_RDBUFF = 0x0c

    SWD_AP_CSW = 0x00
    SWD_AP_TAR = 0x04
    SWD_AP_DRW = 0x0c

    # SWD_AP_DB0 = 0x00 | DAP_TRANSFER_APnDP, // 0x10
    # SWD_AP_DB1 = 0x04 | DAP_TRANSFER_APnDP, // 0x14
    # SWD_AP_DB2 = 0x08 | DAP_TRANSFER_APnDP, // 0x18
    # SWD_AP_DB3 = 0x0c | DAP_TRANSFER_APnDP, // 0x1c

    # SWD_AP_CFG = 0x04 | DAP_TRANSFER_APnDP,  // 0xf4
    # SWD_AP_BASE = 0x08 | DAP_TRANSFER_APnDP, // 0xf8
    # SWD_AP_IDR = 0x0c | DAP_TRANSFER_APnDP,  // 0xfc

    def __init__(self, probe):
        self.probe = probe

    def read_word(self, addr) -> int:
        self.probe.write_ap(DapTarget.SWD_AP_TAR, addr)
        # Post the read and ignore the result.
        self.probe.read_ap(DapTarget.SWD_AP_DRW)
        # Read the RDBUFF to get the last word and not initiate another read.
        return self.probe.read_dp(DapTarget.SWD_DP_R_RDBUFF)

    def write_word(self, addr, data) -> None:
        self.probe.write_ap(DapTarget.SWD_AP_TAR, addr)
        self.probe.write_ap(DapTarget.SWD_AP_DRW, data)
        # Read the RDBUFF to verify the write. (The ack won't be ok if it failed.)
        self.probe.read_dp(DapTarget.SWD_DP_R_RDBUFF)

    def write_reg(self, reg, data):
        if (req & DAP_TRANSFER_APnDP) == 0:
            self.probe.write_dp(reg, data)
        else:
            self.probe.write_ap(reg, data)

    def write_block(self, addr, data) -> None:
        self.probe.write_ap(DapTarget.SWD_AP_TAR, addr)
        words = memoryview(data).cast("I")
        self.probe.write_ap_multiple(DapTarget.SWD_AP_DRW, words)


    def read_block(self, addr, size) -> bytes:
        self.probe.write_ap(DapTarget.SWD_AP_TAR, addr)

        # Post the read and ignore the result.
        self.probe.read_ap(DapTarget.SWD_AP_DRW)

        # We overread by one word because it allows read_ap_multiple to allocate
        # the whole buffer we want to return. This could cause problems if
        # reading past the end of a memory region.
        words = self.probe.read_ap_multiple(DapTarget.SWD_AP_DRW, size // 4)

        # Read the RDBUFF to clear the last word
        self.probe.read_dp(DapTarget.SWD_DP_R_RDBUFF)

        return memoryview(words).cast("B")

    def reset_link(self):
        self.probe.swj_sequence(51, 0xffffffffffffff)
        self.probe.swj_sequence(16, 0xe79e)
        self.probe.swj_sequence(51, 0xffffffffffffff)
        self.probe.swj_sequence(8, 0x00)
        self.probe.read_dp(DapTarget.SWD_DP_R_IDCODE)

    def target_connect(self, swj_clock=50) -> None:
        # First disconnect, in case this really is e reconnect
        self.probe.disconnect()
        self.probe.connect()
        # dap_idle_cycles 0
        # dap_retry_count 128
        # dap_match_retry_count 128

        self.probe.set_clock(swj_clock)
        self.reset_link()

    def target_prepare(self):
        self.probe.write_dp(DapTarget.SWD_DP_W_ABORT, 0xf << 1) # Clear all errors. Bit 0 is dapabort so shift by one.
        self.probe.write_dp(DapTarget.SWD_DP_W_SELECT, 0x00000000) # DP_SELECT_APBANKSEL(0) = 0 | DP_SELECT_APSEL(0) = 0
        self.probe.write_dp(DapTarget.SWD_DP_W_CTRL_STAT, 0x50000f00) # DP_CST_CDBGPWRUPREQ = 0x10000000 | DP_CST_CSYSPWRUPREQ = 0x40000000| DP_CST_MASKLANE(0xf) = 0x0F00
        self.probe.write_ap(DapTarget.SWD_AP_CSW, 0x23000052) # AP_CSW_ADDRINC_SINGLE = 0x10 | AP_CSW_DEVICEEN = 0x40 | AP_CSW_PROT(0x23) = 0x23000000 | AP_CSW_SIZE_WORD = 0x02
 
