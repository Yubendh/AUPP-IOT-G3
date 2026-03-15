# Telegram service: minimal Wi-Fi + Telegram polling and command routing to main.py.

import network
import time
import urequests
import gc
import __main__

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_POLL_SECONDS,
    WIFI_CONNECT_RETRIES,
    WIFI_PASSWORD,
    WIFI_SSID,
)
try:
    handle_command = __main__.handle_command
except AttributeError:
    from main import handle_command

network_lock = getattr(__main__, "network_lock", None)


URL_SEND = "https://api.telegram.org/bot{}/sendMessage".format(TELEGRAM_BOT_TOKEN)
URL_GET_UPDATES = "https://api.telegram.org/bot{}/getUpdates".format(TELEGRAM_BOT_TOKEN)

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
last_update_id = 0
poll_backoff_seconds = 0
updates_initialized = False


def now_ms():
    return time.ticks_ms()


def initialize_update_cursor():
    """Drop old queued Telegram updates so only fresh commands run after boot."""
    global last_update_id, updates_initialized, poll_backoff_seconds

    if updates_initialized:
        return True

    if not ensure_wifi():
        poll_backoff_seconds = min(10, poll_backoff_seconds + 1)
        return False

    gc.collect()
    try:
        print("TG mem before init:", gc.mem_free())
    except AttributeError:
        pass
    response = None
    lock_acquired = False
    try:
        if network_lock is not None:
            network_lock.acquire()
            lock_acquired = True

        # offset=-1 discards backlog and keeps only the newest update cursor.
        response = urequests.get("{}?offset=-1&limit=1".format(URL_GET_UPDATES))
        if response.status_code != 200:
            poll_backoff_seconds = min(10, poll_backoff_seconds + 1)
            return False

        data = response.json()
        if not data.get("ok"):
            poll_backoff_seconds = min(10, poll_backoff_seconds + 1)
            return False

        for update in data.get("result", []):
            last_update_id = update.get("update_id", last_update_id)

        updates_initialized = True
        poll_backoff_seconds = 0
        try:
            print("TG mem after init:", gc.mem_free())
        except AttributeError:
            pass
        print("Telegram cursor initialized:", last_update_id)
        return True
    except Exception as exc:
        try:
            print("TG mem init fail:", gc.mem_free())
        except AttributeError:
            pass
        print("Telegram init cursor error:", exc)
        poll_backoff_seconds = min(10, poll_backoff_seconds + 1)
        return False
    finally:
        if response is not None:
            response.close()
        if lock_acquired:
            network_lock.release()
        gc.collect()


def ensure_wifi():
    if wifi.isconnected():
        return True

    if not wifi.active():
        try:
            wifi.active(True)
            time.sleep_ms(100)
        except Exception as exc:
            print("Telegram Wi-Fi activate error:", exc)
            return False

    try:
        wifi.connect(WIFI_SSID, WIFI_PASSWORD)
    except Exception as exc:
        print("Telegram Wi-Fi connect error:", exc)
        return False

    for _ in range(WIFI_CONNECT_RETRIES):
        if wifi.isconnected():
            return True
        time.sleep(1)
    return False


def send_message(text):
    if not ensure_wifi():
        return False

    gc.collect()
    response = None
    lock_acquired = False
    try:
        if network_lock is not None:
            network_lock.acquire()
            lock_acquired = True
        response = urequests.post(
            URL_SEND,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
        )
        return response.status_code == 200
    except Exception as exc:
        print("Telegram send error:", exc)
        return False
    finally:
        if response is not None:
            response.close()
        if lock_acquired:
            network_lock.release()


def format_status(status_response):
    if not status_response.get("ok"):
        return "Status error."

    data = status_response.get("data", {})
    return (
        "Status\n"
        "gate:{gate_status} {gate_angle}\n"
        "slots:{available_slots}\n"
        "temp:{temp_c}C hum:{humidity_pct}%\n"
        "sys:{system_status}"
    ).format(
        system_status=data.get("system_status", "unknown"),
        gate_status=data.get("gate_status", "unknown"),
        gate_angle=data.get("gate_angle", "unknown"),
        available_slots=data.get("available_slots", "unknown"),
        temp_c=data.get("temp_c", "unknown"),
        humidity_pct=data.get("humidity_pct", "unknown"),
    )


def format_check_response(response):
    if not response.get("ok"):
        return "Failed: {}".format(response.get("error", "unknown_error"))
    return response.get("message", "OK")


def format_slots_response(response):
    if not response.get("ok"):
        return "Failed: {}".format(response.get("error", "unknown_error"))

    data = response.get("data", {})
    return "Slots:{}\n{}".format(
        data.get("available_slots", "unknown"),
        ", ".join(data.get("slots", [])),
    )


def format_temperature_response(response):
    if not response.get("ok"):
        return "Failed: {}".format(response.get("error", "unknown_error"))

    data = response.get("data", {})
    return "Temp:{}C\nHum:{}%".format(
        data.get("temp_c", "unknown"),
        data.get("humidity_pct", "unknown"),
    )


def parse_angle_command(command_text, command_prefix):
    if command_text == command_prefix:
        return {}

    prefix_with_space = command_prefix + " "
    if not command_text.startswith(prefix_with_space):
        return None

    try:
        return {"angle": int(command_text[len(prefix_with_space):].strip())}
    except ValueError:
        return "invalid_angle"


def process_command_text(command_text):
    if command_text == "/status":
        return format_status(handle_command("get_status", source="telegram"))

    open_params = parse_angle_command(command_text, "/open")
    if open_params is not None:
        if open_params == "invalid_angle":
            return "Bad open angle."
        return format_check_response(handle_command("open_gate", source="telegram", params=open_params))

    close_params = parse_angle_command(command_text, "/close")
    if close_params is not None:
        if close_params == "invalid_angle":
            return "Bad close angle."
        return format_check_response(handle_command("close_gate", source="telegram", params=close_params))

    if command_text == "/slots":
        return format_slots_response(handle_command("get_slots", source="telegram"))
    if command_text == "/temp":
        return format_temperature_response(handle_command("get_temp", source="telegram"))
    if command_text == "/light_on":
        return format_check_response(handle_command("light_on", source="telegram"))
    if command_text == "/light_off":
        return format_check_response(handle_command("light_off", source="telegram"))
    if command_text == "/test":
        return "Test"
    return "Bad command."


def poll_updates_once():
    global last_update_id, poll_backoff_seconds

    if not initialize_update_cursor():
        return False

    if not ensure_wifi():
        poll_backoff_seconds = min(10, poll_backoff_seconds + 1)
        return False

    gc.collect()
    response = None
    lock_acquired = False
    updates = []
    try:
        if network_lock is not None:
            network_lock.acquire()
            lock_acquired = True
        # Keep payload small for low-memory boards.
        response = urequests.get(
            "{}?offset={}&limit=1".format(URL_GET_UPDATES, last_update_id + 1)
        )
        if response.status_code != 200:
            poll_backoff_seconds = min(10, poll_backoff_seconds + 1)
            return False

        data = response.json()
        if not data.get("ok"):
            poll_backoff_seconds = min(10, poll_backoff_seconds + 1)
            return False

        updates = data.get("result", [])
        poll_backoff_seconds = 0
    except Exception as exc:
        print("Telegram poll error:", exc)
        poll_backoff_seconds = min(10, poll_backoff_seconds + 1)
        return False
    finally:
        if response is not None:
            response.close()
        if lock_acquired:
            network_lock.release()
        gc.collect()

    for update in updates:
        try:
            last_update_id = update.get("update_id", last_update_id)
            message = update.get("message", {})
            text = message.get("text")
            chat_id = str(message.get("chat", {}).get("id", ""))
            if text and chat_id == str(TELEGRAM_CHAT_ID):
                print("Telegram command:", text)
                send_message(process_command_text(text))
        except Exception as exc:
            print("Telegram command handler error:", exc)
    return True
def run_bot_loop():
    while True:
        poll_updates_once()
        delay = TELEGRAM_POLL_SECONDS + poll_backoff_seconds
        time.sleep(delay)
