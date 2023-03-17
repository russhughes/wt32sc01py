#!/usr/bin/env python3

"""
This script generates two GPIO mask tables to speed up 8-bit parallel output
for the ESP32S3.

The ESP32S3 has 2 sets of 32 bit wide GPIO registers, one set for setting and
another set for clearing the output pins. The bits in registers GPIO_OUT_W1TS_REG
set pins 0-31 and bits in GPIO_OUT1_W1TS_REG set pins 32-48. The bits in
GPIO_OUT_W1TC_REG clear pins 0-31 and the bits in GPIO_OUT1_W1TC_REG clear pins 32-48.

The script creates masks for the data bit pins used for the WT32-SC01 display:
    9, 46, 3, 8, 18, 17, 16,  15

The tables are generated as two lists of 256 32-bit integers, one for each byte
value for both of the GPIO_OUT_W1TS_REG and GPIO_OUT1_W1TS_REG registers.

The values to clear the pins are the complement of the values used to set the
pins. This value can be found by XORing the mask for any value with the mask
for the 255 value. For GPIO_OUT_W1TS_REG this is 0b00000000000001111000001100001000
and for GPIO_OUT1_W1TS_REG this is 0b00000000000000000100000000000000.

In this case, the GPIO_OUT_W1TS_MASK table wastes most of the space it occupies,
since only one 1 bit of the register is ever set or cleared. This could be optimized
by stealing another unused bit in the GPIO_OUT_W1TS_MASK table.  I left it as is
to make it easier to understand and modify for other displays.

"""

GPIO_OUT_W1TS_REG = 0x60004008
GPIO_OUT_W1TC_REG = 0x6000400C
GPIO_OUT1_W1TS_REG =0x60004014
GPIO_OUT1_W1TC_REG =0x60004018

pins = [9, 46, 3, 8, 18, 17, 16,  15]

def make_bytes(value):
    the_bytes = []
    for _ in range(4):
        the_bytes.append(value & 0xff)
        value >>= 8
    return the_bytes

def make_bitmaps(b):

    gpio_out_w1ts = 0
    gpio_out1_w1ts = 0

    # for bit in the byte
    for bit, pin in enumerate(pins):
        if b & (1 << bit):
            if pin < 32:
                gpio_out_w1ts |= (1 << pin)
            else:
                gpio_out1_w1ts |= (1 << (pin - 32))

    return (gpio_out_w1ts, gpio_out1_w1ts)

gpio_out_w1ts_masks = []
gpio_out1_w1ts_masks = []

for i in range(256):
    make_bitmaps(i)
    s0, s1, = make_bitmaps(i)
    gpio_out_w1ts_masks.append(s0)
    gpio_out1_w1ts_masks.append(s1)

print(f"GPIO_OUT_W1TC_MASK = const(0x{gpio_out_w1ts_masks[255]:08x})")
print(f"GPIO_OUT1_W1TC_MASK = const(0x{gpio_out1_w1ts_masks[255]:08x})")
print("# fmt: off")
print("GPIO_OUT_W1TS_MASKS = (\n   ", end="")
for i, mask in enumerate(gpio_out_w1ts_masks):
    print(f"{hex(mask):>8},", end="")
    if i % 4 == 3 and i != 255:
        print("\n   ", end="")
print("\n)")

print("GPIO_OUT1_W1TS_MASKS = (\n   ", end="")
for i, mask in enumerate(gpio_out1_w1ts_masks):
    print(f"{hex(mask):>8},", end="")
    if i % 4 == 3 and i != 255:
        print("\n   ", end="")
print("\n)")
print("# fmt: on")
