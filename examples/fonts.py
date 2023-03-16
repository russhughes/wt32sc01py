"""
fonts.py

    Pages through all characters of four fonts on the display.

"""
from machine import freq
import utime
import wt32sc01py as wt32

# Choose fonts

# import vga1_8x8 as font
import vga2_8x8 as font1

# import vga1_8x16 as font
import vga2_8x16 as font2

# import vga1_16x16 as font
# import vga1_bold_16x16 as font
# import vga2_16x16 as font
import vga2_bold_16x16 as font3

# import vga1_16x32 as font
# import vga1_bold_16x32 as font
# import vga2_16x32 as font
import vga2_bold_16x32 as font4


def main():
    tft = wt32.WT32SC01(0)
    tft.vscrdef(0, 320, 0)

    while True:
        for font in (font1, font2, font3, font4):
            tft.clear()
            line = 0
            col = 0

            for char in range(font.FIRST, font.LAST):
                tft.text(font, chr(char), col, line, wt32.WHITE)
                col += font.WIDTH
                if col > tft.width - font.WIDTH:
                    col = 0
                    line += font.HEIGHT

                    if line > tft.height - font.HEIGHT:
                        utime.sleep(3)
                        tft.clear()
                        line = 0
                        col = 0

            utime.sleep(3)


freq(240_000_000)
main()
