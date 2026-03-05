# Blynk service: sync current datastreams and route gate control through main.

import network
import time
import urequests
import gc
import __main__
import sys

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
try:
    handle_command = __main__.handle_command
except AttributeError:
    from main import handle_command

network_lock = getattr(__main__, "network_lock", None)


wifi = network.WLAN(network.STA_IF)
wifi.active(True)

last_servo_value = None
last_slots_value = None
last_temp_value = None
last_wifi_log_ms = 0
last_force_sync_ms = 0
last_heartbeat_ms = 0
FORCE_SYNC_INTERVAL_MS = 30000


def now_ms():
    return time.ticks_ms()


def ensure_wifi():
    if wifi.isconnected():
        return True

    if not wifi.active():
        try:
            wifi.active(True)
            time.sleep_ms(100)
        except Exception as exc:
            print("Blynk Wi-Fi activate error:", exc)
            return False

    try:
        wifi.connect(WIFI_SSID, WIFI_PASSWORD)
    except Exception as exc:
        print("Blynk Wi-Fi connect error:", exc)
        return False

    for _ in range(WIFI_CONNECT_RETRIES):
        if wifi.isconnected():
            global last_wifi_log_ms
            now = now_ms()
            if time.ticks_diff(now, last_wifi_log_ms) > 30000:
                print("Blynk Wi-Fi connected:", wifi.ifconfig()[0])
                last_wifi_log_ms = now
            return True
        time.sleep(1)
    return False


def blynk_get(vpin):
    if not ensure_wifi():
        return None

    gc.collect()
    response = None
    lock_acquired = False
    try:
        if network_lock is not None:
            network_lock.acquire()
            lock_acquired = True
        response = urequests.get(
            "{}/get?token={}&{}".format(BLYNK_BASE_URL, BLYNK_AUTH_TOKEN, vpin)
        )
        if response.status_code != 200:
            print("Blynk get status:", response.status_code, vpin)
            return None

        return str(response.text).strip().strip('[]"{}')
    except Exception as exc:
        print("Blynk get error:", exc)
        return None
    finally:
        if response is not None:
            response.close()
        if lock_acquired:
            network_lock.release()


def blynk_update(vpin, value):
    if not ensure_wifi():
        return False

    gc.collect()
    response = None
    lock_acquired = False
    try:
        if network_lock is not None:
            network_lock.acquire()
            lock_acquired = True
        response = urequests.get(
            "{}/update?token={}&{}={}".format(BLYNK_BASE_URL, BLYNK_AUTH_TOKEN, vpin, value)
        )
        if response.status_code != 200:
            print("Blynk update status:", response.status_code, vpin, value)
        return response.status_code == 200
    except Exception as exc:
        print("Blynk update error:", exc)
        return False
    finally:
        if response is not None:
            response.close()
        if lock_acquired:
            network_lock.release()


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


def sync_dashboard_outputs(force=False):
    global last_servo_value, last_slots_value, last_temp_value

    gate_switch = get_gate_switch_value()
    if gate_switch is not None and (force or gate_switch != last_servo_value):
        if blynk_update(BLYNK_SERVO_VPIN, gate_switch):
            last_servo_value = gate_switch

    available_slots = get_available_slots_value()
    if available_slots is not None and (force or available_slots != last_slots_value):
        if blynk_update(BLYNK_SLOTS_VPIN, available_slots):
            last_slots_value = available_slots

    temperature = get_temperature_value()
    if temperature is not None and (force or temperature != last_temp_value):
        if blynk_update(BLYNK_TEMPERATURE_VPIN, temperature):
            last_temp_value = temperature


def run_blynk_loop():
    global last_force_sync_ms, last_heartbeat_ms
    print("Starting Blynk loop...")
    while True:
        try:
            if ensure_wifi():
                now = now_ms()
                do_force_sync = time.ticks_diff(now, last_force_sync_ms) > FORCE_SYNC_INTERVAL_MS
                if do_force_sync:
                    last_force_sync_ms = now
                sync_servo_control()
                sync_dashboard_outputs(force=do_force_sync)
                if time.ticks_diff(now, last_heartbeat_ms) > 30000:
                    print("Blynk loop alive.")
                    last_heartbeat_ms = now
            else:
                print("Blynk Wi-Fi connection failed.")
                time.sleep(2)
        except Exception as exc:
            print("Blynk loop error:", exc)
            try:
                sys.print_exception(exc)
            except Exception:
                pass
            gc.collect()
            time.sleep(2)
        time.sleep(BLYNK_POLL_SECONDS)


def run():
    run_blynk_loop()


if __name__ == "__main__":
    run()
