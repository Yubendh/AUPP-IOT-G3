from machine import Pin, PWM
import time

# Motor direction pins
IN1 = Pin(27, Pin.OUT)
IN2 = Pin(26, Pin.OUT)

# PWM pin for speed control
ENA = PWM(Pin(14))
ENA.freq(1000)

def motor_forward(speed):
    IN1.value(1)
    IN2.value(0)
    ENA.duty(speed)


while True:

    print("Forward slow")
    motor_forward(300)
    time.sleep(3)

