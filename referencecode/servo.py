from machine import Pin, PWM
from time import sleep

servo = PWM(Pin(13), freq=50)

while True:
    servo.duty(26)  # set servo to 0 degree
    sleep(2)
    servo.duty(77) # set servo to 90 degree
    sleep(2)
