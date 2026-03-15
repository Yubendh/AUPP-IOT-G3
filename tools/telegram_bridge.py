"""Run a Telegram bot on a computer and bridge commands to the ESP32 over local HTTP.

Environment variables:
- TELEGRAM_BOT_TOKEN: Telegram bot token
- TELEGRAM_CHAT_ID: allowed chat ID
- ESP32_BASE_URL: base URL such as http://192.168.1.50
- TELEGRAM_POLL_SECONDS: optional, defaults to 2
"""

import json
import os
import time
import urllib.parse
import urllib.request


BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ESP32_BASE_URL = os.environ["ESP32_BASE_URL"].rstrip("/")
POLL_SECONDS = float(os.environ.get("TELEGRAM_POLL_SECONDS", "2"))

URL_SEND = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
URL_UPDATES = "https://api.telegram.org/bot{}/getUpdates".format(BOT_TOKEN)

last_update_id = 0


def http_get_json(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def telegram_get_updates(offset):
    query = urllib.parse.urlencode(
        {
            "offset": offset,
            "limit": 5,
            "allowed_updates": json.dumps(["message"]),
            "timeout": 10,
        }
    )
    return http_get_json("{}?{}".format(URL_UPDATES, query), timeout=20)


def telegram_send(text):
    payload = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode("utf-8")
    request = urllib.request.Request(URL_SEND, data=payload, method="POST")
    with urllib.request.urlopen(request, timeout=15) as response:
        response.read()


def esp32_call(path):
    return http_get_json("{}{}".format(ESP32_BASE_URL, path), timeout=10)


def format_status(data):
    info = data.get("data", {})
    return (
        "Gate: {gate}\n"
        "Slots: {slots}\n"
        "Temp: {temp} C\n"
        "Humidity: {hum} %\n"
        "State: {state}"
    ).format(
        gate=info.get("gate_status", "?"),
        slots=info.get("available_slots", "?"),
        temp=info.get("temp_c", "?"),
        hum=info.get("humidity_pct", "?"),
        state=info.get("system_status", "?"),
    )


def handle_command(text):
    text = (text or "").strip()

    if text == "/start":
        return "Commands: /status /open /close /slots /temp"
    if text == "/status":
        return format_status(esp32_call("/api/status"))
    if text == "/open":
        result = esp32_call("/api/open")
        return result.get("message", "Gate opened.")
    if text == "/close":
        result = esp32_call("/api/close")
        return result.get("message", "Gate closed.")
    if text == "/slots":
        result = esp32_call("/api/slots")
        data = result.get("data", {})
        return "Slots: {}\n{}".format(
            data.get("available_slots", "?"),
            ", ".join(data.get("slots", [])),
        )
    if text == "/temp":
        result = esp32_call("/api/temp")
        data = result.get("data", {})
        return "Temp: {} C\nHumidity: {} %".format(
            data.get("temp_c", "?"),
            data.get("humidity_pct", "?"),
        )

    return "Unknown command."


def main():
    global last_update_id

    print("Telegram bridge started.")
    print("ESP32:", ESP32_BASE_URL)
    while True:
        try:
            updates = telegram_get_updates(last_update_id + 1)
            for update in updates.get("result", []):
                last_update_id = update.get("update_id", last_update_id)
                message = update.get("message", {})
                chat_id = str(message.get("chat", {}).get("id", ""))
                text = message.get("text", "")
                if chat_id != str(CHAT_ID):
                    continue
                print("Telegram:", text)
                telegram_send(handle_command(text))
        except Exception as exc:
            print("Bridge error:", exc)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
