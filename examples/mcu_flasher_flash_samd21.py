import array
import board
import digitalio
import time

from adafruit_debug_probe import bitbang
import adafruit_mcu_flasher
from adafruit_mcu_flasher import sam

BASE_ADDR = 0
FILE_BOOTLOADER = "bootloader-metro_m0-v3.15.0.bin"

probe = bitbang.BitbangProbe(
    clk=digitalio.DigitalInOut(board.D12),
    dio=digitalio.DigitalInOut(board.D11),
    nreset=digitalio.DigitalInOut(board.D10)
)
target = sam.SAM(probe)
target.target_connect()
target.select()

print("Erasing... ", end="")
target.erase()
print(" done.")

start = time.monotonic()
target.program_start()

with open(FILE_BOOTLOADER, "rb") as f:
    if FILE_BOOTLOADER.endswith(".bin"):
        adafruit_mcu_flasher.write_bin_file(target, f, BASE_ADDR)
    else:
        adafruit_mcu_flasher.write_hex_file(target, f)

print(f"Done in {time.monotonic()-start:.1f}s")

target.deselect()
probe.disconnect()
