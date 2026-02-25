# Main controller: owns core functions, system state, and outputs consumed by external service modules.

from machine import Pin
import time

from config import IR_OCCUPIED_VALUE, IR_SLOT_PINS


IR_SENSORS = {
    slot_name: Pin(pin_number, Pin.IN)
    for slot_name, pin_number in IR_SLOT_PINS.items()
}


def read_slot_state():
    slots = {}
    available_slots = 0

    for slot_name, sensor in IR_SENSORS.items():
        is_occupied = sensor.value() == IR_OCCUPIED_VALUE
        slots[slot_name] = "occupied" if is_occupied else "free"
        if not is_occupied:
            available_slots += 1

    slots["available_slots"] = available_slots
    return slots


def get_system_output():
    """Return a normalized snapshot for external service modules."""
    slot_state = read_slot_state()
    return {
        "slot_1": slot_state["slot_1"],
        "slot_2": slot_state["slot_2"],
        "slot_3": slot_state["slot_3"],
        "available_slots": slot_state["available_slots"],
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

    return {
        "ok": False,
        "source": source,
        "command": command,
        "error": "unsupported_command",
        "data": {},
    }
