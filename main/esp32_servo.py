import network
import socket
from machine import Pin, PWM
import time

# ── Config ─────────────────────────────────────────────────────────────────────
SSID     = "Robotic WIFI"
PASSWORD = "rbtWIFI@2025"

# Servo pins: index 0 = top (pin 13), index 1 = bottom (pin 17)
SERVO_PINS = [13, 17]

# Set servo angles in degrees (0–180)
ON_ANGLE_TOP    = 0
ON_ANGLE_BOTTOM =   180

OFF_ANGLE_TOP   =   180
OFF_ANGLE_BOTTOM = 0

# Delay between moving top and bottom servo (ms)
SERVO_SEQUENCE_DELAY_MS = 300

# Gestures that trigger each state
GESTURE_ON  = "open_palm"
GESTURE_OFF = "closed_fist"

# ── Hardware ───────────────────────────────────────────────────────────────────
servos = [PWM(Pin(p), freq=50) for p in SERVO_PINS]

def angle_to_duty(deg):
    # Maps 0–180° to duty 26–128 (50 Hz PWM)
    return int(26 + (deg / 180.0) * 102)

def set_servo(idx, deg):
    servos[idx].duty(angle_to_duty(deg))

def apply_state(top_deg, bottom_deg):
    try:
        print("apply_state: top", top_deg, "duty", angle_to_duty(top_deg))
        set_servo(0, top_deg)
        print("apply_state: top done, sleeping")
        time.sleep_ms(SERVO_SEQUENCE_DELAY_MS)
        print("apply_state: bottom", bottom_deg, "duty", angle_to_duty(bottom_deg))
        set_servo(1, bottom_deg)
        print("apply_state: done")
    except BaseException as e:
        print("apply_state ERROR:", e)

# ── State ──────────────────────────────────────────────────────────────────────
# Track current light state so we only act on gesture changes
current_state = None   # None = uninitialised, "on" or "off"

# ── WiFi ───────────────────────────────────────────────────────────────────────
wlan = network.WLAN(network.STA_IF)
wlan.active(False)
time.sleep(0.5)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

print("Connecting to WiFi", end="")
while not wlan.isconnected():
    print(".", end="")
    time.sleep(0.5)

ip = wlan.ifconfig()[0]
print("\nIP:", ip)

# ── HTTP server ────────────────────────────────────────────────────────────────
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("0.0.0.0", 80))
server.listen(5)
server.settimeout(0.05)
print("Listening on http://{}".format(ip))

# Start in OFF position
apply_state(OFF_ANGLE_TOP, OFF_ANGLE_BOTTOM)
current_state = "off"
print("Initialised → OFF")

while True:
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

            if gesture == GESTURE_ON and current_state != "on":
                print("Gesture:", gesture, "→ switching ON")
                apply_state(ON_ANGLE_TOP, ON_ANGLE_BOTTOM)
                current_state = "on"
            elif gesture == GESTURE_OFF and current_state != "off":
                print("Gesture:", gesture, "→ switching OFF")
                apply_state(OFF_ANGLE_TOP, OFF_ANGLE_BOTTOM)
                current_state = "off"
            elif gesture:
                print("Gesture:", gesture, "— no change (already", current_state + ")")

            conn.send("HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK")
        except Exception as e:
            print("ERROR:", e)
        finally:
            conn.close()
    except OSError:
        pass  # socket timeout — normal poll cycle
