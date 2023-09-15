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

from esp32 import RMT
import time
from micropython import const
from machine import mem32, Pin
import ustruct as struct

# memory mapped registers of ESP32S3 for setting and clearing GPIO pins
# see the ESP32S3 datasheet for more information.
GPIO_OUT_W1TS_REG = const(0x60004008)
GPIO_OUT_W1TC_REG = const(0x6000400C)
GPIO_OUT1_W1TS_REG = const(0x60004014)
GPIO_OUT1_W1TC_REG = const(0x60004018)

# see the make_gpio_table script in the utils directory
# of the repository for more information on these tables.
GPIO_OUT_W1TC_MASK = const(0x00078308)
GPIO_OUT1_W1TC_MASK = const(0x00004000)
# fmt: off
GPIO_OUT_W1TS_MASKS = (
        0x0,   0x200,     0x0,   0x200,
        0x8,   0x208,     0x8,   0x208,
      0x100,   0x300,   0x100,   0x300,
      0x108,   0x308,   0x108,   0x308,
    0x40000, 0x40200, 0x40000, 0x40200,
    0x40008, 0x40208, 0x40008, 0x40208,
    0x40100, 0x40300, 0x40100, 0x40300,
    0x40108, 0x40308, 0x40108, 0x40308,
    0x20000, 0x20200, 0x20000, 0x20200,
    0x20008, 0x20208, 0x20008, 0x20208,
    0x20100, 0x20300, 0x20100, 0x20300,
    0x20108, 0x20308, 0x20108, 0x20308,
    0x60000, 0x60200, 0x60000, 0x60200,
    0x60008, 0x60208, 0x60008, 0x60208,
    0x60100, 0x60300, 0x60100, 0x60300,
    0x60108, 0x60308, 0x60108, 0x60308,
    0x10000, 0x10200, 0x10000, 0x10200,
    0x10008, 0x10208, 0x10008, 0x10208,
    0x10100, 0x10300, 0x10100, 0x10300,
    0x10108, 0x10308, 0x10108, 0x10308,
    0x50000, 0x50200, 0x50000, 0x50200,
    0x50008, 0x50208, 0x50008, 0x50208,
    0x50100, 0x50300, 0x50100, 0x50300,
    0x50108, 0x50308, 0x50108, 0x50308,
    0x30000, 0x30200, 0x30000, 0x30200,
    0x30008, 0x30208, 0x30008, 0x30208,
    0x30100, 0x30300, 0x30100, 0x30300,
    0x30108, 0x30308, 0x30108, 0x30308,
    0x70000, 0x70200, 0x70000, 0x70200,
    0x70008, 0x70208, 0x70008, 0x70208,
    0x70100, 0x70300, 0x70100, 0x70300,
    0x70108, 0x70308, 0x70108, 0x70308,
     0x8000,  0x8200,  0x8000,  0x8200,
     0x8008,  0x8208,  0x8008,  0x8208,
     0x8100,  0x8300,  0x8100,  0x8300,
     0x8108,  0x8308,  0x8108,  0x8308,
    0x48000, 0x48200, 0x48000, 0x48200,
    0x48008, 0x48208, 0x48008, 0x48208,
    0x48100, 0x48300, 0x48100, 0x48300,
    0x48108, 0x48308, 0x48108, 0x48308,
    0x28000, 0x28200, 0x28000, 0x28200,
    0x28008, 0x28208, 0x28008, 0x28208,
    0x28100, 0x28300, 0x28100, 0x28300,
    0x28108, 0x28308, 0x28108, 0x28308,
    0x68000, 0x68200, 0x68000, 0x68200,
    0x68008, 0x68208, 0x68008, 0x68208,
    0x68100, 0x68300, 0x68100, 0x68300,
    0x68108, 0x68308, 0x68108, 0x68308,
    0x18000, 0x18200, 0x18000, 0x18200,
    0x18008, 0x18208, 0x18008, 0x18208,
    0x18100, 0x18300, 0x18100, 0x18300,
    0x18108, 0x18308, 0x18108, 0x18308,
    0x58000, 0x58200, 0x58000, 0x58200,
    0x58008, 0x58208, 0x58008, 0x58208,
    0x58100, 0x58300, 0x58100, 0x58300,
    0x58108, 0x58308, 0x58108, 0x58308,
    0x38000, 0x38200, 0x38000, 0x38200,
    0x38008, 0x38208, 0x38008, 0x38208,
    0x38100, 0x38300, 0x38100, 0x38300,
    0x38108, 0x38308, 0x38108, 0x38308,
    0x78000, 0x78200, 0x78000, 0x78200,
    0x78008, 0x78208, 0x78008, 0x78208,
    0x78100, 0x78300, 0x78100, 0x78300,
    0x78108, 0x78308, 0x78108, 0x78308,
)
GPIO_OUT1_W1TS_MASKS = (
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
        0x0,     0x0,  0x4000,  0x4000,
)
# fmt: on


# GPIO Pin Masks for setting and clearing pins
PIN_WR = const(47)
MASK_RESET = const(1 << 4)  # OUT
MASK_DC = const(1)  # OUT
MASK_CS = const(1 << 6)  # OUT
MASK_BACKLIGHT = const(1 << 13)  # OUT1

# ST7796 contoller  commands
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

_ENCODE_PIXEL = const(">H")
_ENCODE_POS = const(">HH")
_DECODE_PIXEL = const(">BBB")

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

        self.wr = Pin(PIN_WR, Pin.OUT, value=1)  # wr
        self.rmt = RMT(1, pin=self.wr, clock_div=5)
        self.pulse = [0, 1]

        self.rst = Pin(4, Pin.OUT)  # reset
        self.dc = Pin(0, Pin.OUT)  # dc
        self.cs = Pin(6, Pin.OUT)  # cs
        self.bl = Pin(45, Pin.OUT)  # backlight0

        self.last = None
        self._rotation = rotation % 4
        self._rotations = rotations

        mem32[GPIO_OUT_W1TS_REG] = MASK_CS
        mem32[GPIO_OUT_W1TS_REG] = MASK_DC

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
            out = GPIO_OUT_W1TS_MASKS[b]
            out1 = GPIO_OUT1_W1TS_MASKS[b]
            mem32[GPIO_OUT_W1TS_REG] = out
            mem32[GPIO_OUT1_W1TS_REG] = out1
            mem32[GPIO_OUT_W1TC_REG] = out ^ GPIO_OUT_W1TC_MASK
            mem32[GPIO_OUT1_W1TC_REG] = out1 ^ GPIO_OUT1_W1TC_MASK
            self.last = b

        self.rmt.write_pulses(2, self.pulse)

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

    # @micropython.native
    def clear(self, color=None):
        """
        Very fast clear screen.

        Args:
            color (bool): True to clear to white, False to clear to black
            or
            color (int): 565 encoded color, with the upper and lower bytes
                being set the same value as color.
        """
        if isinstance(color, bool):
            color = 0xFF if color else 0
        elif color is None:
            color = 0
        else:
            color &= 0xFF

        self._set_window(0, 0, self.width, self.height)

        out = GPIO_OUT_W1TS_MASKS[color]
        out1 = GPIO_OUT1_W1TS_MASKS[color]

        mem32[GPIO_OUT_W1TS_REG] = out
        mem32[GPIO_OUT1_W1TS_REG] = out1
        mem32[GPIO_OUT_W1TC_REG] = out ^ GPIO_OUT_W1TC_MASK
        mem32[GPIO_OUT1_W1TC_REG] = out1 ^ GPIO_OUT1_W1TC_MASK

        mem32[GPIO_OUT_W1TC_REG] = MASK_CS
        mem32[GPIO_OUT_W1TS_REG] = MASK_DC

        pulses = [0, 1] * self.width
        count = self.height + 1

        for _ in range(count * 2):
            self.rmt.write_pulses(2, pulses)
            self.rmt.wait_done()

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

    @micropython.native
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
        wide = font.WIDTH // 8
        fg_hi = color >> 8
        fg_lo = color & 0xFF
        bg_hi = background >> 8
        bg_lo = background & 0xFF

        buffer = bytearray(font.WIDTH * font.HEIGHT * 2)
        for char in text:
            ch = ord(char)
            if (
                font.FIRST <= ch < font.LAST
                and x0 + font.WIDTH <= self.width
                and y0 + font.HEIGHT <= self.height
            ):
                buf_idx = 0
                chr_idx = (ch - font.FIRST) * (font.HEIGHT * wide)
                for _ in range(font.HEIGHT):
                    for _ in range(wide):
                        chr_data = font.FONT[chr_idx]
                        for _ in range(8):
                            if chr_data & 0x80:
                                buffer[buf_idx] = fg_hi
                                buffer[buf_idx + 1] = fg_lo
                            else:
                                buffer[buf_idx] = bg_hi
                                buffer[buf_idx + 1] = bg_lo
                            buf_idx += 2
                            chr_data <<= 1
                        chr_idx += 1

                to_col = x0 + font.WIDTH - 1
                to_row = y0 + font.HEIGHT - 1
                if self.width > to_col and self.height > to_row:
                    self._set_window(x0, y0, to_col, to_row)
                    self._write(None, buffer)

                x0 += font.WIDTH

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
