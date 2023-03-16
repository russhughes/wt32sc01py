"""
chango.py

    Test for font2bitmap converter for the driver.
    See the font2bitmap program in the utils directory.
"""

from machine import freq
import wt32sc01py as wt32
import gc
from truetype import chango_16 as font_16
from truetype import chango_32 as font_32
from truetype import chango_64 as font_64

gc.collect()


def main():
    # enable display and clear screen
    tft = wt32.WT32SC01(0)
    tft.clear()

    row = 0
    tft.write(font_16, "abcdefghijklmnopqrst", 0, row, wt32.RED)
    row += font_16.HEIGHT

    tft.write(font_32, "abcdefghij", 0, row, wt32.GREEN)
    row += font_32.HEIGHT

    tft.write(font_64, "abcd", 0, row, wt32.BLUE)
    row += font_64.HEIGHT


freq(240_000_000)
main()
