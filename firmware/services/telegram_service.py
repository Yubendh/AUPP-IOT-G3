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
        "System Status\n"
        "service: {service}\n"
        "system_status: {system_status}"
    ).format(
        service=data.get("service", "unknown"),
        system_status=data.get("system_status", "unknown"),
    )


def format_check_response(response):
    if not response.get("ok"):
        return "Command failed: {}".format(response.get("error", "unknown_error"))
    return response.get("message", "CHECK: command acknowledged.")


def process_command_text(command_text):
    if command_text == "/status":
        return format_status(handle_command("get_status", source="telegram"))
    if command_text == "/open":
        return format_check_response(handle_command("open_gate", source="telegram"))
    if command_text == "/close":
        return format_check_response(handle_command("close_gate", source="telegram"))
    if command_text == "/slots":
        return format_check_response(handle_command("get_slots", source="telegram"))
    if command_text == "/temp":
        return format_check_response(handle_command("get_temp", source="telegram"))
    if command_text == "/light_on":
        return format_check_response(handle_command("light_on", source="telegram"))
    if command_text == "/light_off":
        return format_check_response(handle_command("light_off", source="telegram"))
    if command_text == "/test":
        return "Test"
    return "Unsupported command. Use /status, /open, /close, /slots, /temp, /light_on, /light_off."


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
