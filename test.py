import network
import urequests
import time
from machine import Pin
import dht

# ---------- WIFI ----------
SSID = "Robotic WIFI"
PASSWORD = "rbtWIFI@2025"

# ---------- TELEGRAM ----------
BOT_TOKEN = "8317214199:AAFkZlexTEuNOvYYAT_mcNOeSshu2Ro0P_k"
CHAT_ID = "-1003317505805"

URL_SEND = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
URL_GET_UPDATES = "https://api.telegram.org/bot{}/getUpdates".format(BOT_TOKEN)

# ---------- DHT22 ----------
DHT_PIN = 4 
sensor = dht.DHT11(Pin(DHT_PIN, Pin.PULL_UP))

# ---------- RELAY ----------
RELAY_PIN = 4 
RELAY_ACTIVE_LOW = True
relay = Pin(RELAY_PIN, Pin.OUT)
relay_state = False

def relay_write(on):
    if RELAY_ACTIVE_LOW:
        relay.value(0 if on else 1)
    else:
        relay.value(1 if on else 0)

relay_write(relay_state)

# ---------- WIFI CONNECT ----------
wifi = network.WLAN(network.STA_IF)
wifi.active(True)

def ensure_wifi():
    if wifi.isconnected():
        return True

    print("Connecting to WiFi...")
    wifi.connect(SSID, PASSWORD)

    for _ in range(15):
        if wifi.isconnected():
            print("WiFi connected")
            return True
        time.sleep(1)

    print("WiFi not connected")
    return False

ensure_wifi()

# Give DHT time to stabilize
time.sleep(2)

# ---------- SEND MESSAGE FUNCTION ----------
def send_message(message):
    if not ensure_wifi():
        return False

    try:
        response = urequests.post(URL_SEND, json={
            "chat_id": CHAT_ID,
            "text": message
        })

        if response.status_code != 200:
            print("Telegram send failed:", response.status_code)
            response.close()
            return False

        print("Message sent:", message)
        response.close()
        return True
    except Exception as e:
        print("Error sending message:", e)
        return False

# ---------- TELEGRAM TEST ----------
send_message("Test")

# ---------- CHECK FOR COMMANDS ----------
last_update_id = 0

def check_commands(temp, hum):
    global last_update_id
    global relay_state
    if not ensure_wifi():
        return False

    try:
        response = urequests.get(URL_GET_UPDATES + "?offset={}".format(last_update_id + 1))
        if response.status_code != 200:
            print("Telegram getUpdates failed:", response.status_code)
            response.close()
            return False

        data = response.json()
        
        if data["ok"] and data["result"]:
            for update in data["result"]:
                last_update_id = update["update_id"]
                
                if "message" in update and "text" in update["message"]:
                    text = update["message"]["text"]
                    print("Received command:", text)
                    
                    if text == "/status":
                        state = "ON" if relay_state else "OFF"
                        msg = "Temperature: {:.2f} °C\nHumidity: {:.2f} %\nRelay: {}".format(temp, hum, state)
                        if not send_message(msg):
                            response.close()
                            return False
                    elif text == "/on":
                        relay_state = True
                        relay_write(relay_state)
                        if not send_message("Relay turned ON"):
                            response.close()
                            return False
                    elif text == "/off":
                        relay_state = False
                        relay_write(relay_state)
                        if not send_message("Relay turned OFF"):
                            response.close()
                            return False
                    elif text == "/test":
                        if not send_message("Test"):
                            response.close()
                            return False
        
        response.close()
        return True
    except Exception as e:
        print("Error checking commands:", e)
        return False

# ---------- MAIN LOOP ----------
TEMP_THRESHOLD = 30.0
auto_off_sent = False

while True:
    try:
        if not ensure_wifi():
            time.sleep(5)
            continue

        time.sleep(2)
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()

        if temp < -40 or temp > 80 or hum < 0 or hum > 100:
            print("Invalid reading: {:.2f} °C | {:.2f} %".format(temp, hum))
        else:
            print("Temperature: {:.2f} °C | Humidity: {:.2f} %".format(temp, hum))

        if not check_commands(temp, hum):
            time.sleep(5)
            continue

        if temp < TEMP_THRESHOLD:
            if relay_state:
                relay_state = False
                relay_write(relay_state)
                if not auto_off_sent:
                    if not send_message("Temperature dropped. Relay auto-OFF"):
                        time.sleep(5)
                        continue
                    auto_off_sent = True
        else:
            auto_off_sent = False
            if not relay_state:
                if not send_message("ALERT: Temperature {:.2f} °C (>= {:.1f}). Send /on to turn relay ON".format(temp, TEMP_THRESHOLD)):
                    time.sleep(5)
                    continue

    except OSError:
        print("Failed to read sensor.")
        time.sleep(5)
        continue
    except Exception as e:
        print("Error:", e)

    time.sleep(5)   



