Python WT32SC01 Plus driver in MicroPython
==========================================

This is a fork of devbis' st7789py_mpy module from
https://github.com/devbis/st7789py_mpy.

This driver adds support for:

- The WT32SC01 Plus 8 bit parallel display
- Display rotation
- Hardware based scrolling
- Drawing text using 8 and 16 bit wide bitmap fonts with heights that are
  multiples of 8.  Included are 12 bitmap fonts derived from classic pc
  BIOS text mode fonts.
- Drawing text using converted TrueType fonts.
- Drawing converted bitmaps

The driver is not fast but it is written in pure MicroPython. It is functional
but is also a work in progress. Documentation can be found in the docs
directory and online at https://penfold.owt.com/wt32sc01py


Examples
--------

See the examples directory for example programs that run on the WT32SC01 Plus.
Some of the examples require additional modules to be available to run, see
the import lines in the examples source code.


Fonts
-----

See the subdirectories in the fonts directory for the converted font modules
used in the examples. These modules can be compiled using the mpy-cross
compiler before uploading to save memory.
