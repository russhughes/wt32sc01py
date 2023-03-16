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
    gpio_out_w1tc = 0
    gpio_out1_w1ts = 0
    gpio_out1_w1tc = 0

    # for bit in the byte
    for bit, pin in enumerate(pins):
        if b & (1 << bit):
            if pin < 32:
                gpio_out_w1ts |= (1 << pin)
            else:
                gpio_out1_w1ts |= (1 << (pin - 32))
        else:
            if pin < 32:
                gpio_out_w1tc |= (1 << pin)
            else:
                gpio_out1_w1tc |= (1 << (pin - 32))

    return (gpio_out_w1ts, gpio_out1_w1ts, gpio_out_w1tc, gpio_out1_w1tc)


out_s0 = []
out_s1 = []
out_c0 = []
out_c1 = []

for i in range(256):
    make_bitmaps(i)
    s0, s1, c0, c1 = make_bitmaps(i)
    out_s0.append(s0)
    out_s1.append(s1)
    out_c0.append(c0)
    out_c1.append(c1)

print("GPIO_OUT_W1TS_REG = ")
for i, mask in enumerate(out_s0):
    print(f"{i:3d}: {mask:032b},")

print("GPIO_OUT1_W1TS_REG = ")
for i, mask in enumerate(out_s1):
    print(f"{i:3d}: {mask:032b},")

print("GPIO_OUT_W1TC_REG = ")
for i, mask in enumerate(out_c0):
    print(f"{i:3d}: {mask:032b},")

print("GPIO_OUT1_W1TC_REG = ")
for i, mask in enumerate(out_c1):
    print(f"{i:3d}: {mask:032b},")
