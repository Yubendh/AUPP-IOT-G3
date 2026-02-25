# Telegram service: minimal Wi-Fi + Telegram polling and command routing to main.py.

import network
import time
import urequests

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_POLL_SECONDS,
    WIFI_CONNECT_RETRIES,
    WIFI_PASSWORD,
    WIFI_SSID,
)
from main import handle_command


URL_SEND = "https://api.telegram.org/bot{}/sendMessage".format(TELEGRAM_BOT_TOKEN)
URL_GET_UPDATES = "https://api.telegram.org/bot{}/getUpdates".format(TELEGRAM_BOT_TOKEN)

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
last_update_id = 0


def ensure_wifi():
    if wifi.isconnected():
        return True

    wifi.connect(WIFI_SSID, WIFI_PASSWORD)
    for _ in range(WIFI_CONNECT_RETRIES):
        if wifi.isconnected():
            return True
        time.sleep(1)
    return False


def send_message(text):
    if not ensure_wifi():
        return False

    response = None
    try:
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


def format_status(status_response):
    if not status_response.get("ok"):
        return "System error: unable to fetch status."

    data = status_response.get("data", {})
    return (
        "Parking Status\n"
        "slot_1: {slot_1}\n"
        "slot_2: {slot_2}\n"
        "slot_3: {slot_3}\n"
        "available_slots: {available_slots}\n"
        "system_status: {system_status}"
    ).format(
        slot_1=data.get("slot_1", "unknown"),
        slot_2=data.get("slot_2", "unknown"),
        slot_3=data.get("slot_3", "unknown"),
        available_slots=data.get("available_slots", "unknown"),
        system_status=data.get("system_status", "unknown"),
    )


def process_command_text(command_text):
    if command_text == "/status":
        return format_status(handle_command("get_status", source="telegram"))
    if command_text == "/refresh":
        return format_status(handle_command("refresh_now", source="telegram"))
    if command_text == "/test":
        return "Test"
    return "Unsupported command."


def poll_updates_once():
    global last_update_id

    if not ensure_wifi():
        return False

    response = None
    try:
        response = urequests.get("{}?offset={}".format(URL_GET_UPDATES, last_update_id + 1))
        if response.status_code != 200:
            return False

        data = response.json()
        if not data.get("ok"):
            return False

        for update in data.get("result", []):
            last_update_id = update.get("update_id", last_update_id)
            message = update.get("message", {})
            text = message.get("text")
            chat_id = str(message.get("chat", {}).get("id", ""))
            if text and chat_id == str(TELEGRAM_CHAT_ID):
                send_message(process_command_text(text))
        return True
    except Exception as exc:
        print("Telegram poll error:", exc)
        return False
    finally:
        if response is not None:
            response.close()


def run_bot_loop():
    while True:
        poll_updates_once()
        time.sleep(TELEGRAM_POLL_SECONDS)
