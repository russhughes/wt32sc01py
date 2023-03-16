"""
Copyright (c) 2020-2023 Russ Hughes

This file incorporates work covered by the following copyright and
permission notice and is licensed under the same terms:

The MIT License (MIT)

Copyright (c) 2019 Ivan Belokobylskiy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

The driver is based on devbis' st7789py_mpy module from
https://github.com/devbis/st7789py_mpy.

This driver adds support for:

- WT32-SC01 Plus 480x320 TFT LCD display
- Display rotation
- Hardware based scrolling
- Drawing text using 8 and 16 bit wide bitmap fonts with heights that are
  multiples of 8.  Included are 12 bitmap fonts derived from classic pc
  BIOS text mode fonts.
- Drawing text using converted TrueType fonts.
- Drawing converted bitmaps

"""

import time
from micropython import const
from machine import mem32, Pin
import ustruct as struct

GPIO_BIT_MASKS = (
    (0, 0, 492296, 16384),
    (512, 0, 491784, 16384),
    (0, 16384, 492296, 0),
    (512, 16384, 491784, 0),
    (8, 0, 492288, 16384),
    (520, 0, 491776, 16384),
    (8, 16384, 492288, 0),
    (520, 16384, 491776, 0),
    (256, 0, 492040, 16384),
    (768, 0, 491528, 16384),
    (256, 16384, 492040, 0),
    (768, 16384, 491528, 0),
    (264, 0, 492032, 16384),
    (776, 0, 491520, 16384),
    (264, 16384, 492032, 0),
    (776, 16384, 491520, 0),
    (262144, 0, 230152, 16384),
    (262656, 0, 229640, 16384),
    (262144, 16384, 230152, 0),
    (262656, 16384, 229640, 0),
    (262152, 0, 230144, 16384),
    (262664, 0, 229632, 16384),
    (262152, 16384, 230144, 0),
    (262664, 16384, 229632, 0),
    (262400, 0, 229896, 16384),
    (262912, 0, 229384, 16384),
    (262400, 16384, 229896, 0),
    (262912, 16384, 229384, 0),
    (262408, 0, 229888, 16384),
    (262920, 0, 229376, 16384),
    (262408, 16384, 229888, 0),
    (262920, 16384, 229376, 0),
    (131072, 0, 361224, 16384),
    (131584, 0, 360712, 16384),
    (131072, 16384, 361224, 0),
    (131584, 16384, 360712, 0),
    (131080, 0, 361216, 16384),
    (131592, 0, 360704, 16384),
    (131080, 16384, 361216, 0),
    (131592, 16384, 360704, 0),
    (131328, 0, 360968, 16384),
    (131840, 0, 360456, 16384),
    (131328, 16384, 360968, 0),
    (131840, 16384, 360456, 0),
    (131336, 0, 360960, 16384),
    (131848, 0, 360448, 16384),
    (131336, 16384, 360960, 0),
    (131848, 16384, 360448, 0),
    (393216, 0, 99080, 16384),
    (393728, 0, 98568, 16384),
    (393216, 16384, 99080, 0),
    (393728, 16384, 98568, 0),
    (393224, 0, 99072, 16384),
    (393736, 0, 98560, 16384),
    (393224, 16384, 99072, 0),
    (393736, 16384, 98560, 0),
    (393472, 0, 98824, 16384),
    (393984, 0, 98312, 16384),
    (393472, 16384, 98824, 0),
    (393984, 16384, 98312, 0),
    (393480, 0, 98816, 16384),
    (393992, 0, 98304, 16384),
    (393480, 16384, 98816, 0),
    (393992, 16384, 98304, 0),
    (65536, 0, 426760, 16384),
    (66048, 0, 426248, 16384),
    (65536, 16384, 426760, 0),
    (66048, 16384, 426248, 0),
    (65544, 0, 426752, 16384),
    (66056, 0, 426240, 16384),
    (65544, 16384, 426752, 0),
    (66056, 16384, 426240, 0),
    (65792, 0, 426504, 16384),
    (66304, 0, 425992, 16384),
    (65792, 16384, 426504, 0),
    (66304, 16384, 425992, 0),
    (65800, 0, 426496, 16384),
    (66312, 0, 425984, 16384),
    (65800, 16384, 426496, 0),
    (66312, 16384, 425984, 0),
    (327680, 0, 164616, 16384),
    (328192, 0, 164104, 16384),
    (327680, 16384, 164616, 0),
    (328192, 16384, 164104, 0),
    (327688, 0, 164608, 16384),
    (328200, 0, 164096, 16384),
    (327688, 16384, 164608, 0),
    (328200, 16384, 164096, 0),
    (327936, 0, 164360, 16384),
    (328448, 0, 163848, 16384),
    (327936, 16384, 164360, 0),
    (328448, 16384, 163848, 0),
    (327944, 0, 164352, 16384),
    (328456, 0, 163840, 16384),
    (327944, 16384, 164352, 0),
    (328456, 16384, 163840, 0),
    (196608, 0, 295688, 16384),
    (197120, 0, 295176, 16384),
    (196608, 16384, 295688, 0),
    (197120, 16384, 295176, 0),
    (196616, 0, 295680, 16384),
    (197128, 0, 295168, 16384),
    (196616, 16384, 295680, 0),
    (197128, 16384, 295168, 0),
    (196864, 0, 295432, 16384),
    (197376, 0, 294920, 16384),
    (196864, 16384, 295432, 0),
    (197376, 16384, 294920, 0),
    (196872, 0, 295424, 16384),
    (197384, 0, 294912, 16384),
    (196872, 16384, 295424, 0),
    (197384, 16384, 294912, 0),
    (458752, 0, 33544, 16384),
    (459264, 0, 33032, 16384),
    (458752, 16384, 33544, 0),
    (459264, 16384, 33032, 0),
    (458760, 0, 33536, 16384),
    (459272, 0, 33024, 16384),
    (458760, 16384, 33536, 0),
    (459272, 16384, 33024, 0),
    (459008, 0, 33288, 16384),
    (459520, 0, 32776, 16384),
    (459008, 16384, 33288, 0),
    (459520, 16384, 32776, 0),
    (459016, 0, 33280, 16384),
    (459528, 0, 32768, 16384),
    (459016, 16384, 33280, 0),
    (459528, 16384, 32768, 0),
    (32768, 0, 459528, 16384),
    (33280, 0, 459016, 16384),
    (32768, 16384, 459528, 0),
    (33280, 16384, 459016, 0),
    (32776, 0, 459520, 16384),
    (33288, 0, 459008, 16384),
    (32776, 16384, 459520, 0),
    (33288, 16384, 459008, 0),
    (33024, 0, 459272, 16384),
    (33536, 0, 458760, 16384),
    (33024, 16384, 459272, 0),
    (33536, 16384, 458760, 0),
    (33032, 0, 459264, 16384),
    (33544, 0, 458752, 16384),
    (33032, 16384, 459264, 0),
    (33544, 16384, 458752, 0),
    (294912, 0, 197384, 16384),
    (295424, 0, 196872, 16384),
    (294912, 16384, 197384, 0),
    (295424, 16384, 196872, 0),
    (294920, 0, 197376, 16384),
    (295432, 0, 196864, 16384),
    (294920, 16384, 197376, 0),
    (295432, 16384, 196864, 0),
    (295168, 0, 197128, 16384),
    (295680, 0, 196616, 16384),
    (295168, 16384, 197128, 0),
    (295680, 16384, 196616, 0),
    (295176, 0, 197120, 16384),
    (295688, 0, 196608, 16384),
    (295176, 16384, 197120, 0),
    (295688, 16384, 196608, 0),
    (163840, 0, 328456, 16384),
    (164352, 0, 327944, 16384),
    (163840, 16384, 328456, 0),
    (164352, 16384, 327944, 0),
    (163848, 0, 328448, 16384),
    (164360, 0, 327936, 16384),
    (163848, 16384, 328448, 0),
    (164360, 16384, 327936, 0),
    (164096, 0, 328200, 16384),
    (164608, 0, 327688, 16384),
    (164096, 16384, 328200, 0),
    (164608, 16384, 327688, 0),
    (164104, 0, 328192, 16384),
    (164616, 0, 327680, 16384),
    (164104, 16384, 328192, 0),
    (164616, 16384, 327680, 0),
    (425984, 0, 66312, 16384),
    (426496, 0, 65800, 16384),
    (425984, 16384, 66312, 0),
    (426496, 16384, 65800, 0),
    (425992, 0, 66304, 16384),
    (426504, 0, 65792, 16384),
    (425992, 16384, 66304, 0),
    (426504, 16384, 65792, 0),
    (426240, 0, 66056, 16384),
    (426752, 0, 65544, 16384),
    (426240, 16384, 66056, 0),
    (426752, 16384, 65544, 0),
    (426248, 0, 66048, 16384),
    (426760, 0, 65536, 16384),
    (426248, 16384, 66048, 0),
    (426760, 16384, 65536, 0),
    (98304, 0, 393992, 16384),
    (98816, 0, 393480, 16384),
    (98304, 16384, 393992, 0),
    (98816, 16384, 393480, 0),
    (98312, 0, 393984, 16384),
    (98824, 0, 393472, 16384),
    (98312, 16384, 393984, 0),
    (98824, 16384, 393472, 0),
    (98560, 0, 393736, 16384),
    (99072, 0, 393224, 16384),
    (98560, 16384, 393736, 0),
    (99072, 16384, 393224, 0),
    (98568, 0, 393728, 16384),
    (99080, 0, 393216, 16384),
    (98568, 16384, 393728, 0),
    (99080, 16384, 393216, 0),
    (360448, 0, 131848, 16384),
    (360960, 0, 131336, 16384),
    (360448, 16384, 131848, 0),
    (360960, 16384, 131336, 0),
    (360456, 0, 131840, 16384),
    (360968, 0, 131328, 16384),
    (360456, 16384, 131840, 0),
    (360968, 16384, 131328, 0),
    (360704, 0, 131592, 16384),
    (361216, 0, 131080, 16384),
    (360704, 16384, 131592, 0),
    (361216, 16384, 131080, 0),
    (360712, 0, 131584, 16384),
    (361224, 0, 131072, 16384),
    (360712, 16384, 131584, 0),
    (361224, 16384, 131072, 0),
    (229376, 0, 262920, 16384),
    (229888, 0, 262408, 16384),
    (229376, 16384, 262920, 0),
    (229888, 16384, 262408, 0),
    (229384, 0, 262912, 16384),
    (229896, 0, 262400, 16384),
    (229384, 16384, 262912, 0),
    (229896, 16384, 262400, 0),
    (229632, 0, 262664, 16384),
    (230144, 0, 262152, 16384),
    (229632, 16384, 262664, 0),
    (230144, 16384, 262152, 0),
    (229640, 0, 262656, 16384),
    (230152, 0, 262144, 16384),
    (229640, 16384, 262656, 0),
    (230152, 16384, 262144, 0),
    (491520, 0, 776, 16384),
    (492032, 0, 264, 16384),
    (491520, 16384, 776, 0),
    (492032, 16384, 264, 0),
    (491528, 0, 768, 16384),
    (492040, 0, 256, 16384),
    (491528, 16384, 768, 0),
    (492040, 16384, 256, 0),
    (491776, 0, 520, 16384),
    (492288, 0, 8, 16384),
    (491776, 16384, 520, 0),
    (492288, 16384, 8, 0),
    (491784, 0, 512, 16384),
    (492296, 0, 0, 16384),
    (491784, 16384, 512, 0),
    (492296, 16384, 0, 0),
)

GPIO_OUT_W1TS_REG = const(0x60004008)
GPIO_OUT_W1TC_REG = const(0x6000400C)
GPIO_OUT1_W1TS_REG = const(0x60004014)
GPIO_OUT1_W1TC_REG = const(0x60004018)

MASK_WR = 1 << 15  # OUT1
MASK_RESET = 1 << 4  # OUT
MASK_DC = 1  # OUT
MASK_CS = 1 << 6  # OUT
MASK_BACKLIGHT = 1 << 13  # OUT1

# commands
ST7796_NOP = const(0x00)
ST7796_SWRESET = const(0x01)
ST7796_RDDID = const(0x04)
ST7796_RDDST = const(0x09)

ST7796_SLPIN = const(0x10)
ST7796_SLPOUT = const(0x11)
ST7796_PTLON = const(0x12)
ST7796_NORON = const(0x13)

ST7796_INVOFF = const(0x20)
ST7796_INVON = const(0x21)
ST7796_DISPOFF = const(0x28)
ST7796_DISPON = const(0x29)
ST7796_CASET = const(0x2A)
ST7796_RASET = const(0x2B)
ST7796_RAMWR = const(0x2C)
ST7796_RAMRD = const(0x2E)

ST7796_PTLAR = const(0x30)
ST7796_VSCRDEF = const(0x33)
ST7796_COLMOD = const(0x3A)
ST7796_MADCTL = const(0x36)
ST7796_VSCSAD = const(0x37)

ST7796_MADCTL_MY = const(0x80)
ST7796_MADCTL_MX = const(0x40)
ST7796_MADCTL_MV = const(0x20)
ST7796_MADCTL_ML = const(0x10)
ST7796_MADCTL_BGR = const(0x08)
ST7796_MADCTL_MH = const(0x04)
ST7796_MADCTL_RGB = const(0x00)

ST7796_RDID1 = const(0xDA)
ST7796_RDID2 = const(0xDB)
ST7796_RDID3 = const(0xDC)
ST7796_RDID4 = const(0xDD)

COLOR_MODE_65K = const(0x50)
COLOR_MODE_262K = const(0x60)
COLOR_MODE_12BIT = const(0x03)
COLOR_MODE_16BIT = const(0x05)
COLOR_MODE_18BIT = const(0x06)
COLOR_MODE_16M = const(0x07)

# Color definitions
BLACK = const(0x0000)
BLUE = const(0x001F)
RED = const(0xF800)
GREEN = const(0x07E0)
CYAN = const(0x07FF)
MAGENTA = const(0xF81F)
YELLOW = const(0xFFE0)
WHITE = const(0xFFFF)

_ENCODE_PIXEL = ">H"
_ENCODE_POS = ">HH"
_DECODE_PIXEL = ">BBB"

_BUFFER_SIZE = const(256)

_BIT7 = const(0x80)
_BIT6 = const(0x40)
_BIT5 = const(0x20)
_BIT4 = const(0x10)
_BIT3 = const(0x08)
_BIT2 = const(0x04)
_BIT1 = const(0x02)
_BIT0 = const(0x01)

# Rotation tables (width, height)[rotation % 4]

WIDTH_480 = [(320, 480), (480, 320), (320, 480), (480, 320)]

# MADCTL ROTATIONS[rotation % 4]
ROTATIONS = [0x48, 0x28, 0x88, 0xE8]


def color565(red, green=0, blue=0):
    """
    Convert red, green and blue values (0-255) into a 16-bit 565 encoding.
    """
    try:
        red, green, blue = red  # see if the first var is a tuple/list
    except TypeError:
        pass
    return (red & 0xF8) << 8 | (green & 0xFC) << 3 | blue >> 3


def _encode_pos(x, y):
    """Encode a postion into bytes."""
    return struct.pack(_ENCODE_POS, x, y)


def _encode_pixel(color):
    """Encode a pixel color into bytes."""
    return struct.pack(_ENCODE_PIXEL, color)


class WT32SC01:
    """
    WT32SC01 driver class

    Args:
        rotation (int): display rotation
            - 0-Portrait
            - 1-Landscape
            - 2-Inverted Portrait
            - 3-Inverted Landscape

        rotations (list): list of rotation values
    """

    def __init__(
        self,
        rotation=0,
        rotations=ROTATIONS,
    ):
        """
        Initialize WT32SC01's st7789 display.
        """

        Pin(15, Pin.OUT)  # d7
        Pin(16, Pin.OUT)  # d6
        Pin(17, Pin.OUT)  # d5
        Pin(18, Pin.OUT)  # d4
        Pin(8, Pin.OUT)  # d3
        Pin(3, Pin.OUT)  # d2
        Pin(46, Pin.OUT)  # d1
        Pin(9, Pin.OUT)  # d0
        self.wr = Pin(47, Pin.OUT)  # wr
        self.rst = Pin(4, Pin.OUT)  # reset
        self.dc = Pin(0, Pin.OUT)  # dc
        self.cs = Pin(6, Pin.OUT)  # cs
        self.bl = Pin(45, Pin.OUT)  # backlight0

        self.last = None
        self._rotation = rotation % 4
        self._rotations = rotations

        mem32[GPIO_OUT_W1TS_REG] = MASK_CS
        mem32[GPIO_OUT_W1TS_REG] = MASK_DC
        mem32[GPIO_OUT1_W1TS_REG] = MASK_WR

        self.hard_reset()
        self.sleep_mode(False)
        self._set_color_mode(COLOR_MODE_65K | COLOR_MODE_16BIT)
        time.sleep_ms(50)
        self.rotation(self._rotation)
        self.inversion_mode(True)
        time.sleep_ms(10)
        self._write(ST7796_NORON)
        time.sleep_ms(10)
        self.backlight_on()
        self._write(ST7796_DISPON)
        time.sleep_ms(125)

    def reset_on(self):
        self.rst.value(1)

    def reset_off(self):
        self.rst.value(0)

    def backlight_on(self):
        self.bl.value(1)

    def backlight_off(self):
        self.bl.value(0)

    @micropython.native
    def _write_byte(self, b):
        """Write to the display using 8 bit parallel mode. Note: this is not fast."""
        if b != self.last:
            mask = GPIO_BIT_MASKS[b]
            mem32[GPIO_OUT_W1TS_REG] = mask[0]
            mem32[GPIO_OUT1_W1TS_REG] = mask[1]
            mem32[GPIO_OUT_W1TC_REG] = mask[2]
            mem32[GPIO_OUT1_W1TC_REG] = mask[3]
            self.last = b

        mem32[GPIO_OUT1_W1TC_REG] = MASK_WR
        mem32[GPIO_OUT1_W1TS_REG] = MASK_WR

    @micropython.native
    def _write(self, command=None, data=None):
        """Write to the display: command and/or data."""

        mem32[GPIO_OUT_W1TC_REG] = MASK_CS

        if command is not None:
            mem32[GPIO_OUT_W1TC_REG] = MASK_DC
            for b in bytes([command]):
                self._write_byte(b)
        if data is not None:
            mem32[GPIO_OUT_W1TS_REG] = MASK_DC
            for b in data:
                self._write_byte(b)

        mem32[GPIO_OUT_W1TS_REG] = MASK_CS

    def hard_reset(self):
        """
        Hard reset display.
        """
        mem32[GPIO_OUT_W1TC_REG] = MASK_CS
        self.reset_on()
        time.sleep_ms(5)
        self.reset_off()
        time.sleep_ms(20)
        self.reset_on()
        time.sleep_ms(150)
        mem32[GPIO_OUT_W1TS_REG] = MASK_CS

    def soft_reset(self):
        """
        Soft reset display.
        """
        self._write(ST7796_SWRESET)
        time.sleep_ms(150)

    def sleep_mode(self, value):
        """
        Enable or disable display sleep mode.

        Args:
            value (bool): if True enable sleep mode. if False disable sleep
            mode
        """
        if value:
            self._write(ST7796_SLPIN)
        else:
            self._write(ST7796_SLPOUT)

    def inversion_mode(self, value):
        """
        Enable or disable display inversion mode.

        Args:
            value (bool): if True enable inversion mode. if False disable
            inversion mode
        """
        if value:
            self._write(ST7796_INVON)
        else:
            self._write(ST7796_INVOFF)

    def _set_color_mode(self, mode):
        """
        Set display color mode.

        Args:
            mode (int): color mode
                COLOR_MODE_65K, COLOR_MODE_262K, COLOR_MODE_12BIT,
                COLOR_MODE_16BIT, COLOR_MODE_18BIT, COLOR_MODE_16M
        """
        self._write(ST7796_COLMOD, bytes([mode & 0x77]))

    def rotation(self, rotation):
        """
        Set display rotation.

        Args:
            rotation (int):
                - 0-Portrait
                - 1-Landscape
                - 2-Inverted Portrait
                - 3-Inverted Landscape
        """

        rotation %= 4
        self._rotation = rotation
        madctl = self._rotations[rotation]
        self.width, self.height = WIDTH_480[rotation]
        self._write(ST7796_MADCTL, bytes([madctl]))

    @micropython.native
    def _set_window(self, x0, y0, x1, y1):
        """
        Set window to column and row address.

        Args:
            x0 (int): column start address
            y0 (int): row start address
            x1 (int): column end address
            y1 (int): row end address
        """
        if x0 <= x1 <= self.width and y0 <= y1 <= self.height:
            self._write(ST7796_CASET, _encode_pos(x0, x1))
            self._write(ST7796_RASET, _encode_pos(y0, y1))
            self._write(ST7796_RAMWR)

    def vline(self, x, y, length, color):
        """
        Draw vertical line at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            length (int): length of line
            color (int): 565 encoded color
        """
        self.fill_rect(x, y, 1, length, color)

    def hline(self, x, y, length, color):
        """
        Draw horizontal line at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            length (int): length of line
            color (int): 565 encoded color
        """
        self.fill_rect(x, y, length, 1, color)

    def pixel(self, x, y, color):
        """
        Draw a pixel at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            color (int): 565 encoded color
        """
        self._set_window(x, y, x, y)
        self._write(None, _encode_pixel(color))

    def blit_buffer(self, buffer, x, y, width, height):
        """
        Copy buffer to display at the given location.

        Args:
            buffer (bytes): Data to copy to display
            x (int): Top left corner x coordinate
            Y (int): Top left corner y coordinate
            width (int): Width
            height (int): Height
        """
        self._set_window(x, y, x + width - 1, y + height - 1)
        self._write(None, buffer)

    def rect(self, x, y, w, h, color):
        """
        Draw a rectangle at the given location, size and color.

        Args:
            x (int): Top left corner x coordinate
            y (int): Top left corner y coordinate
            width (int): Width in pixels
            height (int): Height in pixels
            color (int): 565 encoded color
        """
        self.hline(x, y, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)
        self.hline(x, y + h - 1, w, color)

    @micropython.native
    def fill_rect(self, x, y, width, height, color):
        """
        Draw a rectangle at the given location, size and filled with color.

        Args:
            x (int): Top left corner x coordinate
            y (int): Top left corner y coordinate
            width (int): Width in pixels
            height (int): Height in pixels
            color (int): 565 encoded color
        """
        self._set_window(x, y, x + width - 1, y + height - 1)
        chunks, rest = divmod(width * height, _BUFFER_SIZE)
        pixel = _encode_pixel(color)
        mem32[GPIO_OUT_W1TC_REG] = MASK_CS
        mem32[GPIO_OUT_W1TS_REG] = MASK_DC
        if chunks:
            data = pixel * _BUFFER_SIZE
            for _ in range(chunks):
                self._write(None, data)
        if rest:
            self._write(None, pixel * rest)

        mem32[GPIO_OUT_W1TS_REG] = MASK_CS

    def fill(self, color):
        """
        Fill the entire FrameBuffer with the specified color.

        Args:
            color (int): 565 encoded color
        """
        self.fill_rect(0, 0, self.width, self.height, color)

    @micropython.native
    def clear(self, white=False):
        """
        Fast clear the screen to white if white is True, otherwise black.

        Args:
            white (bool): True to clear to white, False to clear to black

        """

        self._set_window(0, 0, self.width, self.height)
        color = 0xFF if white else 0x00
        mask = GPIO_BIT_MASKS[color]
        mem32[GPIO_OUT_W1TS_REG] = mask[0]
        mem32[GPIO_OUT1_W1TS_REG] = mask[1]
        mem32[GPIO_OUT_W1TC_REG] = mask[2]
        mem32[GPIO_OUT1_W1TC_REG] = mask[3]

        mem32[GPIO_OUT_W1TC_REG] = MASK_CS
        mem32[GPIO_OUT_W1TS_REG] = MASK_DC

        for _ in range(self.width * self.height):
            mem32[GPIO_OUT1_W1TC_REG] = MASK_WR
            mem32[GPIO_OUT1_W1TS_REG] = MASK_WR
            mem32[GPIO_OUT1_W1TC_REG] = MASK_WR
            mem32[GPIO_OUT1_W1TS_REG] = MASK_WR
        mem32[GPIO_OUT_W1TS_REG] = MASK_CS


    @micropython.native
    def line(self, x0, y0, x1, y1, color):
        """
        Draw a single pixel wide line starting at x0, y0 and ending at x1, y1.

        Args:
            x0 (int): Start point x coordinate
            y0 (int): Start point y coordinate
            x1 (int): End point x coordinate
            y1 (int): End point y coordinate
            color (int): 565 encoded color
        """
        steep = abs(y1 - y0) > abs(x1 - x0)
        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0
        dx = x1 - x0
        dy = abs(y1 - y0)
        err = dx // 2
        ystep = 1 if y0 < y1 else -1
        while x0 <= x1:
            if steep:
                self.pixel(y0, x0, color)
            else:
                self.pixel(x0, y0, color)
            err -= dy
            if err < 0:
                y0 += ystep
                err += dx
            x0 += 1

    def vscrdef(self, tfa, vsa, bfa):
        """
        Set Vertical Scrolling Definition.

        To scroll a 135x240 display these values should be 40, 240, 40.
        There are 40 lines above the display that are not shown followed by
        240 lines that are shown followed by 40 more lines that are not shown.
        You could write to these areas off display and scroll them into view by
        changing the TFA, VSA and BFA values.

        Args:
            tfa (int): Top Fixed Area
            vsa (int): Vertical Scrolling Area
            bfa (int): Bottom Fixed Area
        """
        struct.pack(">HHH", tfa, vsa, bfa)
        self._write(ST7796_VSCRDEF, struct.pack(">HHH", tfa, vsa, bfa))

    def vscsad(self, vssa):
        """
        Set Vertical Scroll Start Address of RAM.

        Defines which line in the Frame Memory will be written as the first
        line after the last line of the Top Fixed Area on the display

        Example:

            for line in range(40, 280, 1):
                tft.vscsad(line)
                utime.sleep(0.01)

        Args:
            vssa (int): Vertical Scrolling Start Address

        """
        self._write(ST7796_VSCSAD, struct.pack(">H", vssa))

    def _text8(self, font, text, x0, y0, color=WHITE, background=BLACK):
        """
        Internal method to write characters with width of 8 and
        heights of 8 or 16.

        Yes, this is a lot of code, but it's faster than doing it the easy way.

        Args:
            font (module): font module to use
            text (str): text to write
            x0 (int): column to start drawing at
            y0 (int): row to start drawing at
            color (int): 565 encoded color to use for characters
            background (int): 565 encoded color to use for background
        """
        for char in text:
            ch = ord(char)
            if (
                font.FIRST <= ch < font.LAST
                and x0 + font.WIDTH <= self.width
                and y0 + font.HEIGHT <= self.height
            ):

                if font.HEIGHT == 8:
                    passes = 1
                    size = 8
                    each = 0
                else:
                    passes = 2
                    size = 16
                    each = 8

                for line in range(passes):
                    idx = (ch - font.FIRST) * size + (each * line)
                    buffer = struct.pack(
                        ">64H",
                        color if font.FONT[idx] & _BIT7 else background,
                        color if font.FONT[idx] & _BIT6 else background,
                        color if font.FONT[idx] & _BIT5 else background,
                        color if font.FONT[idx] & _BIT4 else background,
                        color if font.FONT[idx] & _BIT3 else background,
                        color if font.FONT[idx] & _BIT2 else background,
                        color if font.FONT[idx] & _BIT1 else background,
                        color if font.FONT[idx] & _BIT0 else background,
                        color if font.FONT[idx + 1] & _BIT7 else background,
                        color if font.FONT[idx + 1] & _BIT6 else background,
                        color if font.FONT[idx + 1] & _BIT5 else background,
                        color if font.FONT[idx + 1] & _BIT4 else background,
                        color if font.FONT[idx + 1] & _BIT3 else background,
                        color if font.FONT[idx + 1] & _BIT2 else background,
                        color if font.FONT[idx + 1] & _BIT1 else background,
                        color if font.FONT[idx + 1] & _BIT0 else background,
                        color if font.FONT[idx + 2] & _BIT7 else background,
                        color if font.FONT[idx + 2] & _BIT6 else background,
                        color if font.FONT[idx + 2] & _BIT5 else background,
                        color if font.FONT[idx + 2] & _BIT4 else background,
                        color if font.FONT[idx + 2] & _BIT3 else background,
                        color if font.FONT[idx + 2] & _BIT2 else background,
                        color if font.FONT[idx + 2] & _BIT1 else background,
                        color if font.FONT[idx + 2] & _BIT0 else background,
                        color if font.FONT[idx + 3] & _BIT7 else background,
                        color if font.FONT[idx + 3] & _BIT6 else background,
                        color if font.FONT[idx + 3] & _BIT5 else background,
                        color if font.FONT[idx + 3] & _BIT4 else background,
                        color if font.FONT[idx + 3] & _BIT3 else background,
                        color if font.FONT[idx + 3] & _BIT2 else background,
                        color if font.FONT[idx + 3] & _BIT1 else background,
                        color if font.FONT[idx + 3] & _BIT0 else background,
                        color if font.FONT[idx + 4] & _BIT7 else background,
                        color if font.FONT[idx + 4] & _BIT6 else background,
                        color if font.FONT[idx + 4] & _BIT5 else background,
                        color if font.FONT[idx + 4] & _BIT4 else background,
                        color if font.FONT[idx + 4] & _BIT3 else background,
                        color if font.FONT[idx + 4] & _BIT2 else background,
                        color if font.FONT[idx + 4] & _BIT1 else background,
                        color if font.FONT[idx + 4] & _BIT0 else background,
                        color if font.FONT[idx + 5] & _BIT7 else background,
                        color if font.FONT[idx + 5] & _BIT6 else background,
                        color if font.FONT[idx + 5] & _BIT5 else background,
                        color if font.FONT[idx + 5] & _BIT4 else background,
                        color if font.FONT[idx + 5] & _BIT3 else background,
                        color if font.FONT[idx + 5] & _BIT2 else background,
                        color if font.FONT[idx + 5] & _BIT1 else background,
                        color if font.FONT[idx + 5] & _BIT0 else background,
                        color if font.FONT[idx + 6] & _BIT7 else background,
                        color if font.FONT[idx + 6] & _BIT6 else background,
                        color if font.FONT[idx + 6] & _BIT5 else background,
                        color if font.FONT[idx + 6] & _BIT4 else background,
                        color if font.FONT[idx + 6] & _BIT3 else background,
                        color if font.FONT[idx + 6] & _BIT2 else background,
                        color if font.FONT[idx + 6] & _BIT1 else background,
                        color if font.FONT[idx + 6] & _BIT0 else background,
                        color if font.FONT[idx + 7] & _BIT7 else background,
                        color if font.FONT[idx + 7] & _BIT6 else background,
                        color if font.FONT[idx + 7] & _BIT5 else background,
                        color if font.FONT[idx + 7] & _BIT4 else background,
                        color if font.FONT[idx + 7] & _BIT3 else background,
                        color if font.FONT[idx + 7] & _BIT2 else background,
                        color if font.FONT[idx + 7] & _BIT1 else background,
                        color if font.FONT[idx + 7] & _BIT0 else background,
                    )
                    self.blit_buffer(buffer, x0, y0 + 8 * line, 8, 8)

                x0 += 8

    def _text16(self, font, text, x0, y0, color=WHITE, background=BLACK):
        """
        Internal method to draw characters with width of 16 and heights of 16
        or 32.

        Yes, this is a lot of code, but it's faster than doing it the easy way.

        Args:
            font (module): font module to use
            text (str): text to write
            x0 (int): column to start drawing at
            y0 (int): row to start drawing at
            color (int): 565 encoded color to use for characters
            background (int): 565 encoded color to use for background
        """
        for char in text:
            ch = ord(char)
            if (
                font.FIRST <= ch < font.LAST
                and x0 + font.WIDTH <= self.width
                and y0 + font.HEIGHT <= self.height
            ):

                each = 16
                if font.HEIGHT == 16:
                    passes = 2
                    size = 32
                else:
                    passes = 4
                    size = 64

                for line in range(passes):
                    idx = (ch - font.FIRST) * size + (each * line)
                    buffer = struct.pack(
                        ">128H",
                        color if font.FONT[idx] & _BIT7 else background,
                        color if font.FONT[idx] & _BIT6 else background,
                        color if font.FONT[idx] & _BIT5 else background,
                        color if font.FONT[idx] & _BIT4 else background,
                        color if font.FONT[idx] & _BIT3 else background,
                        color if font.FONT[idx] & _BIT2 else background,
                        color if font.FONT[idx] & _BIT1 else background,
                        color if font.FONT[idx] & _BIT0 else background,
                        color if font.FONT[idx + 1] & _BIT7 else background,
                        color if font.FONT[idx + 1] & _BIT6 else background,
                        color if font.FONT[idx + 1] & _BIT5 else background,
                        color if font.FONT[idx + 1] & _BIT4 else background,
                        color if font.FONT[idx + 1] & _BIT3 else background,
                        color if font.FONT[idx + 1] & _BIT2 else background,
                        color if font.FONT[idx + 1] & _BIT1 else background,
                        color if font.FONT[idx + 1] & _BIT0 else background,
                        color if font.FONT[idx + 2] & _BIT7 else background,
                        color if font.FONT[idx + 2] & _BIT6 else background,
                        color if font.FONT[idx + 2] & _BIT5 else background,
                        color if font.FONT[idx + 2] & _BIT4 else background,
                        color if font.FONT[idx + 2] & _BIT3 else background,
                        color if font.FONT[idx + 2] & _BIT2 else background,
                        color if font.FONT[idx + 2] & _BIT1 else background,
                        color if font.FONT[idx + 2] & _BIT0 else background,
                        color if font.FONT[idx + 3] & _BIT7 else background,
                        color if font.FONT[idx + 3] & _BIT6 else background,
                        color if font.FONT[idx + 3] & _BIT5 else background,
                        color if font.FONT[idx + 3] & _BIT4 else background,
                        color if font.FONT[idx + 3] & _BIT3 else background,
                        color if font.FONT[idx + 3] & _BIT2 else background,
                        color if font.FONT[idx + 3] & _BIT1 else background,
                        color if font.FONT[idx + 3] & _BIT0 else background,
                        color if font.FONT[idx + 4] & _BIT7 else background,
                        color if font.FONT[idx + 4] & _BIT6 else background,
                        color if font.FONT[idx + 4] & _BIT5 else background,
                        color if font.FONT[idx + 4] & _BIT4 else background,
                        color if font.FONT[idx + 4] & _BIT3 else background,
                        color if font.FONT[idx + 4] & _BIT2 else background,
                        color if font.FONT[idx + 4] & _BIT1 else background,
                        color if font.FONT[idx + 4] & _BIT0 else background,
                        color if font.FONT[idx + 5] & _BIT7 else background,
                        color if font.FONT[idx + 5] & _BIT6 else background,
                        color if font.FONT[idx + 5] & _BIT5 else background,
                        color if font.FONT[idx + 5] & _BIT4 else background,
                        color if font.FONT[idx + 5] & _BIT3 else background,
                        color if font.FONT[idx + 5] & _BIT2 else background,
                        color if font.FONT[idx + 5] & _BIT1 else background,
                        color if font.FONT[idx + 5] & _BIT0 else background,
                        color if font.FONT[idx + 6] & _BIT7 else background,
                        color if font.FONT[idx + 6] & _BIT6 else background,
                        color if font.FONT[idx + 6] & _BIT5 else background,
                        color if font.FONT[idx + 6] & _BIT4 else background,
                        color if font.FONT[idx + 6] & _BIT3 else background,
                        color if font.FONT[idx + 6] & _BIT2 else background,
                        color if font.FONT[idx + 6] & _BIT1 else background,
                        color if font.FONT[idx + 6] & _BIT0 else background,
                        color if font.FONT[idx + 7] & _BIT7 else background,
                        color if font.FONT[idx + 7] & _BIT6 else background,
                        color if font.FONT[idx + 7] & _BIT5 else background,
                        color if font.FONT[idx + 7] & _BIT4 else background,
                        color if font.FONT[idx + 7] & _BIT3 else background,
                        color if font.FONT[idx + 7] & _BIT2 else background,
                        color if font.FONT[idx + 7] & _BIT1 else background,
                        color if font.FONT[idx + 7] & _BIT0 else background,
                        color if font.FONT[idx + 8] & _BIT7 else background,
                        color if font.FONT[idx + 8] & _BIT6 else background,
                        color if font.FONT[idx + 8] & _BIT5 else background,
                        color if font.FONT[idx + 8] & _BIT4 else background,
                        color if font.FONT[idx + 8] & _BIT3 else background,
                        color if font.FONT[idx + 8] & _BIT2 else background,
                        color if font.FONT[idx + 8] & _BIT1 else background,
                        color if font.FONT[idx + 8] & _BIT0 else background,
                        color if font.FONT[idx + 9] & _BIT7 else background,
                        color if font.FONT[idx + 9] & _BIT6 else background,
                        color if font.FONT[idx + 9] & _BIT5 else background,
                        color if font.FONT[idx + 9] & _BIT4 else background,
                        color if font.FONT[idx + 9] & _BIT3 else background,
                        color if font.FONT[idx + 9] & _BIT2 else background,
                        color if font.FONT[idx + 9] & _BIT1 else background,
                        color if font.FONT[idx + 9] & _BIT0 else background,
                        color if font.FONT[idx + 10] & _BIT7 else background,
                        color if font.FONT[idx + 10] & _BIT6 else background,
                        color if font.FONT[idx + 10] & _BIT5 else background,
                        color if font.FONT[idx + 10] & _BIT4 else background,
                        color if font.FONT[idx + 10] & _BIT3 else background,
                        color if font.FONT[idx + 10] & _BIT2 else background,
                        color if font.FONT[idx + 10] & _BIT1 else background,
                        color if font.FONT[idx + 10] & _BIT0 else background,
                        color if font.FONT[idx + 11] & _BIT7 else background,
                        color if font.FONT[idx + 11] & _BIT6 else background,
                        color if font.FONT[idx + 11] & _BIT5 else background,
                        color if font.FONT[idx + 11] & _BIT4 else background,
                        color if font.FONT[idx + 11] & _BIT3 else background,
                        color if font.FONT[idx + 11] & _BIT2 else background,
                        color if font.FONT[idx + 11] & _BIT1 else background,
                        color if font.FONT[idx + 11] & _BIT0 else background,
                        color if font.FONT[idx + 12] & _BIT7 else background,
                        color if font.FONT[idx + 12] & _BIT6 else background,
                        color if font.FONT[idx + 12] & _BIT5 else background,
                        color if font.FONT[idx + 12] & _BIT4 else background,
                        color if font.FONT[idx + 12] & _BIT3 else background,
                        color if font.FONT[idx + 12] & _BIT2 else background,
                        color if font.FONT[idx + 12] & _BIT1 else background,
                        color if font.FONT[idx + 12] & _BIT0 else background,
                        color if font.FONT[idx + 13] & _BIT7 else background,
                        color if font.FONT[idx + 13] & _BIT6 else background,
                        color if font.FONT[idx + 13] & _BIT5 else background,
                        color if font.FONT[idx + 13] & _BIT4 else background,
                        color if font.FONT[idx + 13] & _BIT3 else background,
                        color if font.FONT[idx + 13] & _BIT2 else background,
                        color if font.FONT[idx + 13] & _BIT1 else background,
                        color if font.FONT[idx + 13] & _BIT0 else background,
                        color if font.FONT[idx + 14] & _BIT7 else background,
                        color if font.FONT[idx + 14] & _BIT6 else background,
                        color if font.FONT[idx + 14] & _BIT5 else background,
                        color if font.FONT[idx + 14] & _BIT4 else background,
                        color if font.FONT[idx + 14] & _BIT3 else background,
                        color if font.FONT[idx + 14] & _BIT2 else background,
                        color if font.FONT[idx + 14] & _BIT1 else background,
                        color if font.FONT[idx + 14] & _BIT0 else background,
                        color if font.FONT[idx + 15] & _BIT7 else background,
                        color if font.FONT[idx + 15] & _BIT6 else background,
                        color if font.FONT[idx + 15] & _BIT5 else background,
                        color if font.FONT[idx + 15] & _BIT4 else background,
                        color if font.FONT[idx + 15] & _BIT3 else background,
                        color if font.FONT[idx + 15] & _BIT2 else background,
                        color if font.FONT[idx + 15] & _BIT1 else background,
                        color if font.FONT[idx + 15] & _BIT0 else background,
                    )
                    self.blit_buffer(buffer, x0, y0 + 8 * line, 16, 8)
            x0 += font.WIDTH

    def text(self, font, text, x0, y0, color=WHITE, background=BLACK):
        """
        Draw text on display in specified font and colors. 8 and 16 bit wide
        fonts are supported.

        Args:
            font (module): font module to use.
            text (str): text to write
            x0 (int): column to start drawing at
            y0 (int): row to start drawing at
            color (int): 565 encoded color to use for characters
            background (int): 565 encoded color to use for background
        """
        if font.WIDTH == 8:
            self._text8(font, text, x0, y0, color, background)
        else:
            self._text16(font, text, x0, y0, color, background)

    @micropython.native
    def bitmap(self, bitmap, x, y, index=0):
        """
        Draw a bitmap on display at the specified column and row

        Args:
            bitmap (bitmap_module): The module containing the bitmap to draw
            x (int): column to start drawing at
            y (int): row to start drawing at
            index (int): Optional index of bitmap to draw from multiple bitmap
                module

        """
        bitmap_size = bitmap.HEIGHT * bitmap.WIDTH
        buffer_len = bitmap_size * 2
        buffer = bytearray(buffer_len)
        bs_bit = bitmap.BPP * bitmap_size * index if index > 0 else 0

        for i in range(0, buffer_len, 2):
            color_index = 0
            for _ in range(bitmap.BPP):
                color_index <<= 1
                color_index |= (
                    bitmap.BITMAP[bs_bit // 8] & 1 << (7 - (bs_bit % 8))
                ) > 0
                bs_bit += 1

            color = bitmap.PALETTE[color_index]
            buffer[i + 1] = (color & 0xFF00) >> 8
            buffer[i] = color & 0xFF

        to_col = x + bitmap.WIDTH - 1
        to_row = y + bitmap.HEIGHT - 1
        if self.width > to_col and self.height > to_row:
            self._set_window(x, y, to_col, to_row)
            self._write(None, buffer)

    @micropython.native
    def write(self, font, string, x, y, fg=WHITE, bg=BLACK):
        """
        Write a string using a converted true-type font on the display starting
        at the specified column and row

        Args:
            font (font): The module containing the converted true-type font
            s (string): The string to write
            x (int): column to start writing
            y (int): row to start writing
            fg (int): foreground color, optional, defaults to WHITE
            bg (int): background color, optional, defaults to BLACK
        """
        buffer_len = font.HEIGHT * font.MAX_WIDTH * 2
        buffer = bytearray(buffer_len)
        fg_hi = (fg & 0xFF00) >> 8
        fg_lo = fg & 0xFF

        bg_hi = (bg & 0xFF00) >> 8
        bg_lo = bg & 0xFF

        for character in string:
            try:
                char_index = font.MAP.index(character)
                offset = char_index * font.OFFSET_WIDTH
                bs_bit = font.OFFSETS[offset]
                if font.OFFSET_WIDTH > 1:
                    bs_bit = (bs_bit << 8) + font.OFFSETS[offset + 1]

                if font.OFFSET_WIDTH > 2:
                    bs_bit = (bs_bit << 8) + font.OFFSETS[offset + 2]

                char_width = font.WIDTHS[char_index]
                buffer_needed = char_width * font.HEIGHT * 2

                for i in range(0, buffer_needed, 2):
                    if font.BITMAPS[bs_bit // 8] & 1 << (7 - (bs_bit % 8)) > 0:
                        buffer[i] = fg_hi
                        buffer[i + 1] = fg_lo
                    else:
                        buffer[i] = bg_hi
                        buffer[i + 1] = bg_lo

                    bs_bit += 1

                to_col = x + char_width - 1
                to_row = y + font.HEIGHT - 1
                if self.width > to_col and self.height > to_row:
                    self._set_window(x, y, to_col, to_row)
                    self._write(None, buffer[:buffer_needed])

                x += char_width

            except ValueError:
                pass

    def write_width(self, font, string):
        """
        Returns the width in pixels of the string if it was written with the
        specified font

        Args:
            font (font): The module containing the converted true-type font
            string (string): The string to measure
        """
        width = 0
        for character in string:
            try:
                char_index = font.MAP.index(character)
                width += font.WIDTHS[char_index]

            except ValueError:
                pass

        return width
