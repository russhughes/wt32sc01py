"""
hello.py

    Writes "Hello!" in random colors at random locations on the display.

"""
from machine import freq
import random
import wt32sc01py as wt32

# Choose a font

# import vga1_8x8 as font
# import vga2_8x8 as font
# import vga1_8x16 as font
# import vga2_8x16 as font
# import vga1_16x16 as font
# import vga1_bold_16x16 as font
# import vga2_16x16 as font
# import vga2_bold_16x16 as font
# import vga1_16x32 as font
# import vga1_bold_16x32 as font
# import vga2_16x32 as font
import vga2_bold_16x32 as font


def main():
    tft = wt32.WT32SC01(0)

    while True:
        for rotation in range(4):
            tft.rotation(rotation)
            tft.clear(random.getrandbits(8))

            col_max = tft.width - font.WIDTH * 6
            row_max = tft.height - font.HEIGHT

            for _ in range(50):
                tft.text(
                    font,
                    "Hello!",
                    random.randint(0, col_max),
                    random.randint(0, row_max),
                    wt32.color565(
                        random.getrandbits(8),
                        random.getrandbits(8),
                        random.getrandbits(8),
                    ),
                    wt32.color565(
                        random.getrandbits(8),
                        random.getrandbits(8),
                        random.getrandbits(8),
                    ),
                )


freq(240_000_000)
main()
