from machine import Pin, I2C
import time
import tcs34725

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = tcs34725.TCS34725(i2c)

print("Place object in front of sensor")

while True:

    r,g,b,c = sensor.read_raw()

    print("R:",r," G:",g," B:",b)

    time.sleep(1)
