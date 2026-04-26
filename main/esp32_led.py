import network
import socket
import neopixel
from machine import Pin, SoftI2C, time_pulse_us
from machine_i2c_lcd import I2cLcd
import time

# ── Config ─────────────────────────────────────────────────────────────────────
SSID       = "Brewie Coffee GF"
PASSWORD   = "brewie2024"
LED_PIN    = 23
NUM_LEDS   = 24
TRIG_PIN   = 27
ECHO_PIN   = 26
SDA_PIN    = 21
SCL_PIN    = 22
I2C_ADDR   = 0x27
THRESHOLD  = 30  # cm — object must be within this range

# ── Gesture → colour ───────────────────────────────────────────────────────────
COLOURS = {
    "point_index": (255, 0,   0),
    "peace_sign":  (0,   0, 255),
    "thumb_up":    (0, 255,   0),
}
OFF = (0, 0, 0)

# ── Hardware setup ─────────────────────────────────────────────────────────────
led  = neopixel.NeoPixel(Pin(LED_PIN), NUM_LEDS)
trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)
i2c  = SoftI2C(sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400000)
lcd  = I2cLcd(i2c, I2C_ADDR, 2, 16)

def pad(s, n=16):
    s = str(s)
    return s + " " * (n - len(s)) if len(s) < n else s[:n]

def set_all(colour):
    for i in range(NUM_LEDS):
        led[i] = colour
    led.write()

def get_distance_cm():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    duration = time_pulse_us(echo, 1, 30000)
    if duration < 0:
        return None
    return (duration * 0.0343) / 2

def update_lcd(distance, active):
    if distance is None:
        line1 = "Distance:--- cm "
    else:
        d = int(distance)
        line1 = pad("Distance:" + str(d) + " cm")
    line2 = pad("Status: ON " if active else "Status: OFF")
    lcd.move_to(0, 0)
    lcd.putstr(line1)
    lcd.move_to(0, 1)
    lcd.putstr(line2)

# ── WiFi ───────────────────────────────────────────────────────────────────────
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

lcd.clear()
lcd.move_to(0, 0)
lcd.putstr("Connecting WiFi ")

print("Connecting to WiFi", end="")
while not wlan.isconnected():
    print(".", end="")
    time.sleep(0.5)

ip = wlan.ifconfig()[0]
print("\nIP:", ip)
lcd.move_to(0, 1)
lcd.putstr(pad(ip))
time.sleep(2)

# ── HTTP server ────────────────────────────────────────────────────────────────
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("0.0.0.0", 80))
server.listen(5)
server.settimeout(0.5)  # allows LCD to refresh even when idle
print("Listening on http://{}".format(ip))

set_all(OFF)

while True:
    distance = get_distance_cm()
    active   = distance is not None and distance < THRESHOLD
    update_lcd(distance, active)

    try:
        conn, addr = server.accept()
        try:
            request = conn.recv(256).decode()
            gesture = None
            if "GET /gesture" in request:
                for part in request.split():
                    if part.startswith("/gesture?name="):
                        gesture = part.split("=", 1)[1]
                        break

            if gesture:
                if active:
                    colour = COLOURS.get(gesture, OFF)
                    set_all(colour)
                    print("Gesture:", gesture, "->", colour, "dist:", distance)
                else:
                    set_all(OFF)
                    print("Gesture:", gesture, "ignored — out of range, dist:", distance)

            conn.send("HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK")
        except:
            pass
        finally:
            conn.close()
    except OSError:
        pass  # socket timeout — normal poll cycle
