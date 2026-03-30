from machine import Pin
import neopixel
import time

led = neopixel.NeoPixel(Pin(23), 16)

def wheel(pos):
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

while True:
    for j in range(255):
        for i in range(16):
            led[i] = wheel((i + j) & 255)
        led.write()

