"""
toasters.py

    An example using bitmap to draw sprites on the display.

    Spritesheet from CircuitPython_Flying_Toasters
    https://learn.adafruit.com/circuitpython-sprite-animation-pendant-mario-clouds-flying-toasters

"""

import random
from machine import freq, Pin, SoftSPI
import wt32sc01py as wt32
import t1, t2, t3, t4, t5

TOASTERS = [t1, t2, t3, t4]
TOAST = [t5]
WIDTH = 480


class toast:
    """
    toast class to keep track of a sprites locaton and step
    """

    def __init__(self, sprites, x, y):
        self.sprites = sprites
        self.steps = len(sprites)
        self.x = x
        self.y = y
        self.step = random.randint(0, self.steps - 1)
        self.speed = random.randint(2, 5)

    def move(self):
        if self.x <= 0:
            self.speed = random.randint(2, 5)
            self.x = WIDTH - 64

        self.step += 1
        self.step %= self.steps
        self.x -= self.speed


def main():
    """
    Initialize the display and draw flying toasters and toast
    """
    tft = wt32.WT32SC01(1)
    tft.clear()

    # create toast spites in random positions
    sprites = [
        toast(TOASTERS, WIDTH - 64, 32),
        toast(TOAST, WIDTH - 64 * 2, 128),
        toast(TOASTERS, WIDTH - 64 * 4, 224),
    ]

    # move and draw sprites
    while True:
        for man in sprites:
            bitmap = man.sprites[man.step]
            tft.fill_rect(
                man.x + bitmap.WIDTH - man.speed,
                man.y,
                man.speed,
                bitmap.HEIGHT,
                wt32.BLACK,
            )

            man.move()

            if man.x > 0:
                tft.bitmap(bitmap, man.x, man.y)
            else:
                tft.fill_rect(0, man.y, bitmap.WIDTH, bitmap.HEIGHT, wt32.BLACK)


freq(240_000_000)
main()
