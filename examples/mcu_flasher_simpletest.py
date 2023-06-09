"""Verifies the flash contents of a SAMD51."""

import array
import board
import digitalio
import time

from adafruit_debug_probe import bitbang
import adafruit_mcu_flasher
from adafruit_mcu_flasher import samx5

BASE_ADDR = 0
FILE_BOOTLOADER = "bootloader-metro_m4-v3.15.0.bin"

probe = bitbang.BitbangProbe(
    clk=digitalio.DigitalInOut(board.D12),
    dio=digitalio.DigitalInOut(board.D11),
    nreset=digitalio.DigitalInOut(board.D10),
    drive_mode=digitalio.DriveMode.PUSH_PULL
)
target = samx5.SAMx5(probe)
target.target_connect()
target.select()

start = time.monotonic()

with open(FILE_BOOTLOADER, "rb") as f:
    if FILE_BOOTLOADER.endswith(".bin"):
        adafruit_mcu_flasher.write_bin_file(target, f, BASE_ADDR, verify_only=True)
    else:
        adafruit_mcu_flasher.write_hex_file(target, f, verify_only=True)

print(f"Done in {time.monotonic()-start:.1f}s")

target.deselect()
probe.disconnect()
