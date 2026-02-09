import network
import time
import machine
import urequests as requests
from tm1637 import TM1637

# ---------- CONFIG ----------
WIFI_SSID = "Robotic WIFI"
WIFI_PASS = "rbtWIFI@2025"

BLYNK_TOKEN = "IjdA92t_vgrLogCy0R_vIqhvSPxfUkW4"
BLYNK_API   = "http://blynk.cloud/external/api"

IR_PIN    = 12
SERVO_PIN = 13
TM_CLK    = 17
TM_DIO    = 16

# ---------- HARDWARE ----------
ir = machine.Pin(IR_PIN, machine.Pin.IN)
servo = machine.PWM(machine.Pin(SERVO_PIN), freq=50)
tm = TM1637(clk_pin=TM_CLK, dio_pin=TM_DIO, brightness=5)

# ---------- WIFI ----------
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASS)

print("Connecting to WiFi...")
while not wifi.isconnected():
    time.sleep(1)
print("WiFi connected!")

# ---------- BLYNK ----------
def send_ir_status_v0(detected):
    url = f"{BLYNK_API}/update?token={BLYNK_TOKEN}&V0={detected}"
    r = requests.get(url)
    r.close()

def read_slider_v1():
    r = requests.get(f"{BLYNK_API}/get?token={BLYNK_TOKEN}&V1")
    value = int(str(r.text).strip('[]"{}'))
    r.close()
    return value

def angle_to_duty(angle):
    return int(26 + (angle / 180) * 102)

def send_counter_v2(count):
    url = f"{BLYNK_API}/update?token={BLYNK_TOKEN}&V2={count}"
    r = requests.get(url)
    r.close()

def read_mode_v3():
    r = requests.get(f"{BLYNK_API}/get?token={BLYNK_TOKEN}&V3")
    value = int(str(r.text).strip('[]"{}'))
    r.close()
    return value

# ---------- MAIN ----------
print("Running IR sensor + Servo control...")

counter = 0
last_ir = 1  # track previous IR state (1 = no obstacle)
tm.show_digit(counter)

while True:
    auto_mode = read_mode_v3() == 1
    current_ir = ir.value()

    if auto_mode:
        if current_ir == 0:
            print("Obstacle detected")
            send_ir_status_v0(1)

            if last_ir == 1:
                counter += 1
                print("Counter:", counter)
                tm.show_digit(counter)
                send_counter_v2(counter)

            servo.duty(angle_to_duty(90))
            print("Servo opened to 90°")
            time.sleep(3)
            servo.duty(angle_to_duty(0))
            print("Servo closed to 0°")
        else:
            print("No obstacle")
            send_ir_status_v0(0)
    else:
        print("Manual mode - IR ignored")

    last_ir = current_ir

    angle = read_slider_v1()
    angle = max(0, min(180, angle))
    servo.duty(angle_to_duty(angle))
    print("Servo angle:", angle)

    time.sleep(2)

