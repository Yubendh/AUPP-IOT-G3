# Main controller: Telegram-focused command and status interface.

import time
try:
    import _thread
except ImportError:
    _thread = None
try:
    import machine
except ImportError:
    machine = None

from config import (
    ENABLE_BLYNK_SERVICE,
    ENABLE_TELEGRAM_SERVICE,
    ENABLE_WEBSERVER_SERVICE,
    SERVO_CLOSE_ANGLE,
    SERVO_FREQ,
    SERVO_OPEN_ANGLE,
    SERVO_PIN,
)

gate_status = "CLOSED"
gate_angle = SERVO_CLOSE_ANGLE
servo = None


def get_servo():
    global servo

    if servo is not None:
        return servo

    if machine is None:
        return None

    servo = machine.PWM(machine.Pin(SERVO_PIN), freq=SERVO_FREQ)
    return servo


def clamp_angle(angle):
    return max(0, min(180, int(angle)))


def angle_to_duty(angle):
    angle = clamp_angle(angle)
    return int(26 + (angle / 180) * 102)


def set_gate_position(target_angle, label, source):
    global gate_status, gate_angle

    bounded_angle = clamp_angle(target_angle)
    servo_motor = get_servo()
    if servo_motor is None:
        print("Servo debug [{}]: hardware unavailable, requested {} at {} degrees".format(source, label, bounded_angle))
        gate_status = label
        gate_angle = bounded_angle
        return False

    servo_motor.duty(angle_to_duty(bounded_angle))
    gate_status = label
    gate_angle = bounded_angle
    print("Servo debug [{}]: {} gate to {} degrees".format(source, label.lower(), bounded_angle))
    return True


def get_system_output():
    """Return a minimal system snapshot for Telegram responses."""
    return {
        "service": "telegram_bot",
        "system_status": "running",
        "gate_status": gate_status,
        "gate_angle": gate_angle,
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
        angle = params.get("angle", SERVO_OPEN_ANGLE)
        servo_ok = set_gate_position(angle, "OPEN", source)
        return {
            "ok": servo_ok or machine is None,
            "source": source,
            "command": command,
            "message": "Gate open command set to {} degrees.".format(clamp_angle(angle)),
            "data": {
                "gate_status": gate_status,
                "servo_angle": gate_angle,
            },
        }

    if command == "close_gate":
        angle = params.get("angle", SERVO_CLOSE_ANGLE)
        servo_ok = set_gate_position(angle, "CLOSED", source)
        return {
            "ok": servo_ok or machine is None,
            "source": source,
            "command": command,
            "message": "Gate close command set to {} degrees.".format(clamp_angle(angle)),
            "data": {
                "gate_status": gate_status,
                "servo_angle": gate_angle,
            },
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
