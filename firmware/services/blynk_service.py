# Blynk service: sync current datastreams and route gate control through main.

import network
import time
import urequests

from config import (
    BLYNK_AUTH_TOKEN,
    BLYNK_BASE_URL,
    BLYNK_POLL_SECONDS,
    BLYNK_SERVO_VPIN,
    BLYNK_SLOTS_VPIN,
    BLYNK_TEMPERATURE_VPIN,
    WIFI_CONNECT_RETRIES,
    WIFI_PASSWORD,
    WIFI_SSID,
)
from main import handle_command


wifi = network.WLAN(network.STA_IF)
wifi.active(True)

last_servo_value = None


def ensure_wifi():
    if wifi.isconnected():
        return True

    wifi.connect(WIFI_SSID, WIFI_PASSWORD)
    for _ in range(WIFI_CONNECT_RETRIES):
        if wifi.isconnected():
            return True
        time.sleep(1)
    return False


def blynk_get(vpin):
    if not ensure_wifi():
        return None

    response = None
    try:
        response = urequests.get(
            "{}/get?token={}&{}".format(BLYNK_BASE_URL, BLYNK_AUTH_TOKEN, vpin)
        )
        if response.status_code != 200:
            return None

        return str(response.text).strip().strip('[]"{}')
    except Exception as exc:
        print("Blynk get error:", exc)
        return None
    finally:
        if response is not None:
            response.close()


def blynk_update(vpin, value):
    if not ensure_wifi():
        return False

    response = None
    try:
        response = urequests.get(
            "{}/update?token={}&{}={}".format(BLYNK_BASE_URL, BLYNK_AUTH_TOKEN, vpin, value)
        )
        return response.status_code == 200
    except Exception as exc:
        print("Blynk update error:", exc)
        return False
    finally:
        if response is not None:
            response.close()


def parse_switch_value(value):
    if value is None:
        return None

    if value in ("0", "1"):
        return int(value)

    return None


def get_available_slots_value():
    response = handle_command("get_slots", source="blynk")
    if not response.get("ok"):
        return None

    data = response.get("data", {})
    available_slots = data.get("available_slots")
    if isinstance(available_slots, int):
        return max(0, min(4, available_slots))

    slots = data.get("slots")
    if isinstance(slots, list):
        available = 0
        for status in slots:
            if status == "OPEN":
                available += 1
        return max(0, min(4, available))

    return None


def get_temperature_value():
    response = handle_command("get_temp", source="blynk")
    if not response.get("ok"):
        return None

    temp_value = response.get("data", {}).get("temp_c")
    if isinstance(temp_value, (int, float)):
        return max(0, min(100, float(temp_value)))

    return None


def get_gate_switch_value():
    response = handle_command("get_status", source="blynk")
    if not response.get("ok"):
        return None

    gate_status = response.get("data", {}).get("gate_status")
    if gate_status == "OPEN":
        return 1
    if gate_status == "CLOSED":
        return 0
    return None


def sync_servo_control():
    global last_servo_value

    servo_value = parse_switch_value(blynk_get(BLYNK_SERVO_VPIN))
    if servo_value is None or servo_value == last_servo_value:
        return

    if servo_value == 1:
        handle_command("open_gate", source="blynk")
    else:
        handle_command("close_gate", source="blynk")

    last_servo_value = servo_value


def sync_dashboard_outputs():
    global last_servo_value

    gate_switch = get_gate_switch_value()
    if gate_switch is not None:
        blynk_update(BLYNK_SERVO_VPIN, gate_switch)
        last_servo_value = gate_switch

    available_slots = get_available_slots_value()
    if available_slots is not None:
        blynk_update(BLYNK_SLOTS_VPIN, available_slots)

    temperature = get_temperature_value()
    if temperature is not None:
        blynk_update(BLYNK_TEMPERATURE_VPIN, temperature)


def run_blynk_loop():
    if not ensure_wifi():
        print("Blynk Wi-Fi connection failed.")
        return

    print("Starting Blynk loop...")
    while True:
        sync_servo_control()
        sync_dashboard_outputs()
        time.sleep(BLYNK_POLL_SECONDS)


def run():
    run_blynk_loop()


if __name__ == "__main__":
    run()
