from machine import Pin
import neopixel
import time

led = neopixel.NeoPixel(Pin(23), 16)

while True:

    led[0] = (255,0,0)  # RED
    led.write()
    time.sleep(1)

    led[1] = (0,255,0)  # GREEN
    led.write()
    time.sleep(1)

    led[2] = (0,0,255)  # BLUE
    led.write()
    time.sleep(1)