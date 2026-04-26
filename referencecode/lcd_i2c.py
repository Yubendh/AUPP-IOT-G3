from machine import Pin, SoftI2C
from machine_i2c_lcd import I2cLcd
from time import sleep

I2C_ADDR = 0x27
i2c = SoftI2C(sda=Pin(21), scl=Pin(22), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

lcd.clear()
lcd.move_to(0, 0)         # first row
lcd.putstr("IoT course")
lcd.move_to(0, 1)         # second row
lcd.putstr("Welcome to AUPP")