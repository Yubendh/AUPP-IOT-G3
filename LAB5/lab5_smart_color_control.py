import network
import socket
import time
from machine import I2C, Pin, PWM
import neopixel
from tcs34527 import TCS34725

# =========================
# WiFi Configuration
# =========================
SSID = "Robotic WIFI"
PASSWORD = "rbtWIFI@2025"

# =========================
# Hardware Pin Configuration
# =========================
I2C_SCL = 22
I2C_SDA = 21

NEOPIXEL_PIN = 23
NEOPIXEL_COUNT = 24

MOTOR_IN1_PIN = 27
MOTOR_IN2_PIN = 26
MOTOR_PWM_PIN = 14
MOTOR_PWM_FREQ = 1000

# =========================
# LAB Rules
# =========================
AUTO_SPEED = {
    "RED": 700,
    "GREEN": 500,
    "BLUE": 300,
}

AUTO_PIXEL = {
    "RED": (255, 0, 0),
    "GREEN": (0, 255, 0),
    "BLUE": (0, 0, 255),
}

# =========================
# Global Runtime State
# =========================
mode = "AUTO"
manual_rgb = (255, 255, 255)
manual_speed = 500

last_r = 0
last_g = 0
last_b = 0
last_c = 0
last_color = "UNKNOWN"

# =========================
# Hardware Setup
# =========================
i2c = I2C(0, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=100000)
sensor = TCS34725(i2c)

pixels = neopixel.NeoPixel(Pin(NEOPIXEL_PIN), NEOPIXEL_COUNT)
for i in range(NEOPIXEL_COUNT):
    pixels[i] = (0, 0, 0)
pixels.write()

motor_in1 = Pin(MOTOR_IN1_PIN, Pin.OUT)
motor_in2 = Pin(MOTOR_IN2_PIN, Pin.OUT)
motor_pwm = PWM(Pin(MOTOR_PWM_PIN))
motor_pwm.freq(MOTOR_PWM_FREQ)


def set_all_pixels(rgb):
    for i in range(NEOPIXEL_COUNT):
        pixels[i] = rgb
    pixels.write()


def motor_forward(speed):
    motor_in1.value(1)
    motor_in2.value(0)
    motor_pwm.duty(speed)


def motor_backward(speed):
    motor_in1.value(0)
    motor_in2.value(1)
    motor_pwm.duty(speed)


def motor_stop():
    motor_in1.value(0)
    motor_in2.value(0)
    motor_pwm.duty(0)


def classify_color(r, g, b, c):
    if c < 150:
        return "UNKNOWN"
    if r > g and r > b:
        return "RED"
    if g > r and g > b:
        return "GREEN"
    if b > r and b > g:
        return "BLUE"
    return "UNKNOWN"


def apply_auto_outputs(color_name):
    if color_name in AUTO_PIXEL:
        set_all_pixels(AUTO_PIXEL[color_name])
    else:
        set_all_pixels((0, 0, 0))

    speed = AUTO_SPEED.get(color_name, 0)
    if speed > 0:
        motor_forward(speed)
    else:
        motor_stop()


def connect_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    if not wifi.isconnected():
        wifi.connect(SSID, PASSWORD)
        print("Connecting to WiFi", end="")
        while not wifi.isconnected():
            print(".", end="")
            time.sleep(0.3)
    print("\nWiFi connected")
    print("ESP32 IP:", wifi.ifconfig()[0])
    return wifi


def parse_query(path):
    if "?" not in path:
        return {}
    query = path.split("?", 1)[1]
    params = {}
    for pair in query.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            params[key] = value
    return params


def handle_http(path):
    global mode, manual_rgb, manual_speed

    if path.startswith("/set_speed"):
        params = parse_query(path)
        try:
            speed = int(float(params.get("speed", "500")))
            speed = max(0, min(1023, speed))
            manual_speed = speed
            return "text/plain", "SPEED SET"
        except Exception:
            return "text/plain", "INVALID SPEED"

    if path.startswith("/forward"):
        mode = "MANUAL"
        motor_forward(manual_speed)
        return "text/plain", "FORWARD"

    if path.startswith("/backward"):
        mode = "MANUAL"
        motor_backward(manual_speed)
        return "text/plain", "BACKWARD"

    if path.startswith("/stop"):
        mode = "MANUAL"
        motor_stop()
        return "text/plain", "STOP"

    if path.startswith("/set_rgb"):
        mode = "MANUAL"
        params = parse_query(path)
        try:
            r = int(params.get("r", "0"))
            g = int(params.get("g", "0"))
            b = int(params.get("b", "0"))
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            manual_rgb = (r, g, b)
            set_all_pixels(manual_rgb)
            return "text/plain", "RGB SET"
        except Exception:
            return "text/plain", "INVALID RGB"

    if path.startswith("/set_mode"):
        params = parse_query(path)
        requested = params.get("mode", "AUTO").upper()
        if requested in ("AUTO", "MANUAL"):
            mode = requested
            return "text/plain", "MODE " + mode
        return "text/plain", "INVALID MODE"

    if path.startswith("/status"):
        body = (
            '{"mode":"%s","color":"%s","r":%d,"g":%d,"b":%d,"c":%d}'
            % (mode, last_color, last_r, last_g, last_b, last_c)
        )
        return "application/json", body

    return "text/plain", "ESP32 LAB5 READY"


def serve_client(server_sock):
    try:
        client, addr = server_sock.accept()
    except OSError:
        return

    try:
        request = client.recv(1024)
        if not request:
            client.close()
            return

        request_str = request.decode()
        first_line = request_str.split("\r\n", 1)[0]
        parts = first_line.split(" ")
        if len(parts) < 2:
            client.close()
            return

        path = parts[1]
        content_type, body = handle_http(path)

        header = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: %s\r\n"
            "Connection: close\r\n\r\n" % content_type
        )
        client.send(header)
        client.send(body)

        print("HTTP", path, "->", body)
    except Exception as ex:
        print("HTTP error:", ex)
    finally:
        client.close()


def start_server():
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # ADD THIS
    server.bind(addr)
    server.listen(2)
    server.settimeout(0.05)
    print("HTTP server running on", addr)
    return server

def main():
    global last_r, last_g, last_b, last_c, last_color

    connect_wifi()
    server = start_server()

    print("Default mode = AUTO")
    last_scan = 0

    while True:
        now = time.ticks_ms()

        if time.ticks_diff(now, last_scan) >= 2000:
            r, g, b, c = sensor.read_raw()
            color_name = classify_color(r, g, b, c)

            last_r = r
            last_g = g
            last_b = b
            last_c = c
            last_color = color_name

            print("RGBC:", r, g, b, c, "=>", color_name, "Mode:", mode)
            print()

            if mode == "AUTO":
                apply_auto_outputs(color_name)

            last_scan = time.ticks_ms()

        serve_client(server)


main()
