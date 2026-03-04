# Main controller: Telegram-focused command and status interface.

import time
try:
    import _thread
except ImportError:
    _thread = None

from config import (
    ENABLE_BLYNK_SERVICE,
    ENABLE_TELEGRAM_SERVICE,
    ENABLE_WEBSERVER_SERVICE,
)


def get_system_output():
    """Return a minimal system snapshot for Telegram responses."""
    return {
        "service": "telegram_bot",
        "system_status": "running",
        "last_update": time.ticks_ms(),
    }


def handle_command(command, source="unknown", params=None):
    """Command entry point for Telegram/Web/Blynk service modules."""
    if params is None:
        params = {}

    if command == "get_status":
        return {
            "ok": True,
            "source": source,
            "command": command,
            "data": get_system_output(),
        }

    if command == "refresh_now":
        return {
            "ok": True,
            "source": source,
            "command": command,
            "data": get_system_output(),
        }

    if command == "open_gate":
        return {
            "ok": True,
            "source": source,
            "command": command,
            "message": "CHECK: gate open command received.",
            "data": {},
        }

    if command == "close_gate":
        return {
            "ok": True,
            "source": source,
            "command": command,
            "message": "CHECK: gate close command received.",
            "data": {},
        }

    if command == "get_slots":
        return {
            "ok": True,
            "source": source,
            "command": command,
            "message": "CHECK: slot query received.",
            "data": {"available_slots": "CHECK_ONLY"},
        }

    if command == "get_temp":
        return {
            "ok": True,
            "source": source,
            "command": command,
            "message": "CHECK: temperature query received.",
            "data": {"temp_c": "CHECK_ONLY"},
        }

    if command == "light_on":
        return {
            "ok": True,
            "source": source,
            "command": command,
            "message": "CHECK: light on command received.",
            "data": {},
        }

    if command == "light_off":
        return {
            "ok": True,
            "source": source,
            "command": command,
            "message": "CHECK: light off command received.",
            "data": {},
        }

    return {
        "ok": False,
        "source": source,
        "command": command,
        "error": "unsupported_command",
        "data": {},
    }


def run():
    """Start enabled service loops when main.py is executed directly."""
    service_starters = []

    if ENABLE_WEBSERVER_SERVICE:
        try:
            from services.webserver_service import run_webserver_loop
        except ImportError:
            from webserver_service import run_webserver_loop
        service_starters.append(("webserver", run_webserver_loop))

    if ENABLE_BLYNK_SERVICE:
        try:
            from services.blynk_service import run_blynk_loop
        except ImportError:
            from blynk_service import run_blynk_loop
        service_starters.append(("blynk", run_blynk_loop))

    if ENABLE_TELEGRAM_SERVICE:
        try:
            from services.telegram_service import run_bot_loop
        except ImportError:
            from telegram_service import run_bot_loop
        service_starters.append(("telegram", run_bot_loop))

    if not service_starters:
        print("No services enabled.")
        return

    if len(service_starters) > 1 and _thread is None:
        print("Threading unavailable; starting only {} service.".format(service_starters[0][0]))
        service_starters[0][1]()
        return

    for service_name, service_runner in service_starters[:-1]:
        print("Starting {} service...".format(service_name))
        _thread.start_new_thread(service_runner, ())

    service_name, service_runner = service_starters[-1]
    print("Starting {} service...".format(service_name))
    service_runner()


if __name__ == "__main__":
    run()
