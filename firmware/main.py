# Main controller: Telegram-focused command and status interface.

import time


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
    """Start Telegram bot loop when main.py is executed directly."""
    try:
        from services.telegram_service import run_bot_loop
    except ImportError:
        from telegram_service import run_bot_loop

    print("Starting Telegram bot loop...")
    run_bot_loop()


if __name__ == "__main__":
    run()
