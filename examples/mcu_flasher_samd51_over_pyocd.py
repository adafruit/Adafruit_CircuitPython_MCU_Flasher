"""This example tries to flash a SAMD51 over a PyOCD probe but doesn't work
   with a JLink. JLink errors out on writing the TAR register on the AP."""

import array
import logging
import sys
import time

from pyocd.core.session import Session
from pyocd.core.helpers import ConnectHelper
from adafruit_mcu_flasher import samx5

logging.basicConfig(level=logging.INFO)

BASE_ADDR = 0

probe = ConnectHelper.choose_probe()
session = Session(probe=probe, options={"jlink.device": "ATSAMD51J20"})
probe.open() # Connects to the probe hardware. Reads capabilities
print(probe)

# probe.connect() # Initializes the probe's pins to the target.
target = samx5.SAMx5(probe)
target.target_connect()
target.select()

print("Erasing... ", end="")
target.erase()
print(" done.")

start = time.monotonic()
target.program_start()

with open(FILE_BOOTLOADER, "rb") as f:
    if FILE_BOOTLOADER.endswith(".bin"):
        write_bin_file(target, f, BASE_ADDR)
    else:
        write_hex_file(target, f)

print(f"Done in {time.monotonic()-start:.1f}s")

target.deselect()
probe.disconnect()
