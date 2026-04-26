import network
import socket
from machine import Pin, PWM
import time

# ── Config ─────────────────────────────────────────────────────────────────────
SSID     = "Brewie Coffee GF"
PASSWORD = "brewie2024"

# Servo pins
SERVO_PINS = [13, 17]

# Duty values (50Hz PWM): duty(26)=0°, duty(77)=90°, duty(128)=180°
SERVO_REST_DUTY = [77, 77]   # neutral position (90°)
SERVO_FLIP_DUTY = [26, 26]   # flip position (0°) — adjust per physical mount

FLIP_HOLD_MS = 1500   # ms to hold at flip angle before returning
COOLDOWN_MS  = 500    # ms after returning before accepting next gesture

# Which gesture triggers which servo (index 0 or 1)
GESTURE_MAP = {
    "open_palm":   0,
    "closed_fist": 1,
}

# ── Hardware ───────────────────────────────────────────────────────────────────
servos = [PWM(Pin(p), freq=50) for p in SERVO_PINS]

def set_servo(idx, duty):
    servos[idx].duty(duty)

# ── State machine ──────────────────────────────────────────────────────────────
IDLE     = 0
FLIPPING = 1   # at flip angle, waiting to return
COOLDOWN = 2   # returned, brief cooldown before accepting again

servo_state = [IDLE, IDLE]
servo_timer = [0, 0]

def any_busy():
    return any(s != IDLE for s in servo_state)

def start_flip(idx):
    set_servo(idx, SERVO_FLIP_DUTY[idx])
    servo_state[idx] = FLIPPING
    servo_timer[idx] = time.ticks_ms()
    print("Servo", idx + 1, "flipping")

def update_servos():
    now = time.ticks_ms()
    for i in range(2):
        if servo_state[i] == FLIPPING:
            if time.ticks_diff(now, servo_timer[i]) >= FLIP_HOLD_MS:
                set_servo(i, SERVO_REST_DUTY[i])
                servo_state[i] = COOLDOWN
                servo_timer[i] = now
                print("Servo", i + 1, "returning")
        elif servo_state[i] == COOLDOWN:
            if time.ticks_diff(now, servo_timer[i]) >= COOLDOWN_MS:
                servo_state[i] = IDLE
                print("Servo", i + 1, "ready")

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
server.settimeout(0.05)  # short timeout so servo state updates stay responsive
print("Listening on http://{}".format(ip))

for i in range(2):
    set_servo(i, SERVO_REST_DUTY[i])

while True:
    update_servos()

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
                idx = GESTURE_MAP.get(gesture)
                if idx is not None:
                    if not any_busy():
                        start_flip(idx)
                    else:
                        print("Gesture", gesture, "ignored — servo busy")

            conn.send("HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK")
        except:
            pass
        finally:
            conn.close()
    except OSError:
        pass  # socket timeout — normal
