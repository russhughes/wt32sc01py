"""
scroll.py

    Smoothly scrolls all font characters up the screen on the display.

"""
from machine import freq
import utime
import random
import wt32sc01py as wt32

# choose a font

# import vga1_8x8 as font
# import vga2_8x8 as font
# import vga1_8x16 as font
# import vga2_8x16 as font
# import vga1_16x16 as font
# import vga1_bold_16x16 as font
# import vga2_16x16 as font
import vga2_bold_16x16 as font


def main():
    tft = wt32.WT32SC01(0)
    tft.clear()

    last_line = tft.height - font.HEIGHT
    tft.vscrdef(0, 320, 0)

    scroll = 0
    character = 0
    while True:
        tft.fill_rect(0, scroll, tft.width, 1, wt32.BLACK)

        if scroll % font.HEIGHT == 0:
            tft.text(
                font,
                "0x{:02x}= {:s} ".format(character, chr(character)),
                96,
                (scroll + last_line) % tft.height,
                wt32.WHITE,
                wt32.BLACK,
            )

            character = character + 1 if character < 256 else 0

        tft.vscsad(scroll)
        scroll += 1

        if scroll == tft.height:
            scroll = 0

        utime.sleep(0.01)


main()
