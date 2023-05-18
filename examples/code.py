import array
import board
import digitalio
import time

from adafruit_debug_probe import bitbang
from adafruit_mcu_flasher import nrf5x

BASE_ADDR = 0
FILE_BOOTLOADER = "bl.hex"
BUFSIZE = 1024

UICR_BOOTLOADER         = 0x10001014
UICR_BOOTLOADER_VAL     = 0x000F4000
UICR_MBR_PARAM_PAGE     = 0x10001018
UICR_MBR_PARAM_PAGE_VAL = 0x000FE000

def write_bin_file(target, file, addr):
    print("Programming... ")

    charcount = 0
    to_write = file.read(BUFSIZE)
    while to_write:
        if charcount % 64 == 0:
            if charcount > 0:
                duration = time.monotonic() - start_time
                print(f" {duration:.1f}s")
            print(f"{addr:08x}", end="")
            start_time = time.monotonic()

        if not target.program_flash(addr, to_write):
           print(f"Failed writing at 0x{addr:08x}!")
           break

        addr += len(to_write)
        charcount += 1
        print(".", end="")
        to_write = file.read(BUFSIZE)
    print("")

def write_hex_file(target, file):
    print("Programming... ")

    charcount = 0
    line_buf = bytearray(24)
    buf = bytearray(BUFSIZE)
    for i in range(len(buf)):
        buf[i] = 0xff
    buf_address = 0
    last_write_address = None
    for line in file:
        if line[0] != ord(b":"):
            continue
        for b in range(1, len(line) - 1, 2):
            line_buf[b // 2] = int(line[b:b+2], 16)
        record_type = line_buf[3]
        if record_type == 0:
            address = base_address | line_buf[1] << 8 | line_buf[2]
            bytecount = line_buf[0]
            if address + bytecount > buf_address + len(buf):
                # if last_write_address is not None:
                #     print("i", hex(buf_address), hex(last_write_address), (buf_address - last_write_address) // BUFSIZE)
                if (last_write_address is None or
                    ((buf_address - last_write_address) // BUFSIZE) >= 64):
                    if last_write_address is not None:
                        duration = time.monotonic() - start_time
                        print(f" {duration:.1f}s")
                    print(f"{buf_address:08x}", end="")
                    last_write_address = buf_address
                    start_time = time.monotonic()

                print(".", end="")
                if not target.program_flash(buf_address, buf):
                   print(f"Failed writing at 0x{buf_address:08x}!")
                   break
                buf_address = address
                for i in range(len(buf)):
                    buf[i] = 0xff
            offset = address - buf_address
            buf[offset:offset+bytecount] = line_buf[4:4+bytecount]
            # print("write", hex(address))
            pass # data
        elif record_type == 3:
            pass # start of execution
        elif record_type == 1:
            # end of file
            if not target.program_flash(buf_address, buf):
               print(f"Failed writing at 0x{buf_address:08x}!")
               break
        elif record_type == 4:
            base_address = line_buf[4] << 24
            base_address |= line_buf[5] << 16
        else:
            print("record type", record_type)
            print(line_buf)

    duration = time.monotonic() - start_time
    print(f" {duration:.1f}s")

probe = bitbang.BitbangProbe(clk=digitalio.DigitalInOut(board.D12), dio=digitalio.DigitalInOut(board.D11), nreset=digitalio.DigitalInOut(board.D10))
target = nrf5x.NRF(probe)
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

# Write UICR setting
target.program_uicr(UICR_BOOTLOADER, UICR_BOOTLOADER_VAL)
target.program_uicr(UICR_MBR_PARAM_PAGE, UICR_MBR_PARAM_PAGE_VAL)

print(f"Done in {time.monotonic()-start:.1f}s")

target.deselect()
probe.disconnect()
