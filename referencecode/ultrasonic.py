from machine import Pin, time_pulse_us
import time

# Pin configuration
TRIG = Pin(27, Pin.OUT)
ECHO = Pin(26, Pin.IN)

def get_distance_cm():
    # Ensure trigger is LOW
    TRIG.value(0)
    time.sleep_us(2)

    # Send 10µs pulse
    TRIG.value(1)
    time.sleep_us(10)
    TRIG.value(0)

    # Measure echo pulse duration
    duration = time_pulse_us(ECHO, 1, 30000)  # timeout = 30ms

    # Check for timeout
    if duration < 0:
        return None

    # Distance calculation (cm)
    distance = (duration * 0.0343) / 2
    return distance

# Main loop
while True:
    dist = get_distance_cm()
    if dist is not None:
        print("Distance: {:.2f} cm".format(dist))
    else:
        print("Out of range")

    time.sleep(1)
