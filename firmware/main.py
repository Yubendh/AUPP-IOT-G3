"""Main controller: shared hardware state and command routing for all services."""

import sys
import time

try:
    import _thread
except ImportError:
    _thread = None

try:
    import machine
    import dht
except ImportError:
    machine = None
    dht = None

from config import (
    AUTO_GATE_OPEN_MS,
    CONTROL_LOOP_DELAY_MS,
    DHT11_PIN,
    ENABLE_BLYNK_SERVICE,
    ENABLE_TELEGRAM_SERVICE,
    ENABLE_WEBSERVER_SERVICE,
    ENTRY_DISTANCE_CM,
    IR_SENSOR_ACTIVE_LOW,
    IR_SENSOR_USE_PULLUP,
    IR_SLOT_PINS,
    LCD_COLS,
    LCD_EVENT_HOLD_MS,
    LCD_I2C_ADDR,
    LCD_I2C_FREQ,
    LCD_ROWS,
    LCD_SCL_PIN,
    LCD_SDA_PIN,
    MAX_SLOTS,
    SERVO_CLOSE_ANGLE,
    SERVO_FREQ,
    SERVO_OPEN_ANGLE,
    SERVO_PIN,
    TM1637_BRIGHTNESS,
    TM1637_CLK_PIN,
    TM1637_DIO_PIN,
    ULTRASONIC_ECHO_PIN,
    ULTRASONIC_TIMEOUT_US,
    ULTRASONIC_TRIG_PIN,
)

for extra_path in ("hardware", "/hardware", "services", "/services"):
    if extra_path not in sys.path:
        sys.path.append(extra_path)

try:
    from tm1637 import TM1637
except ImportError:
    from hardware.tm1637 import TM1637

try:
    from machine_i2c_lcd import I2cLcd
except ImportError:
    from hardware.machine_i2c_lcd import I2cLcd


hardware = {
    "servo": None,
    "trig": None,
    "echo": None,
    "slot_pins": [],
    "dht": None,
    "tm1637": None,
    "lcd": None,
}

state = {
    "service": "parking_controller",
    "system_status": "starting",
    "gate_status": "CLOSED",
    "gate_angle": SERVO_CLOSE_ANGLE,
    "relay_status": "DISABLED",
    "slot_statuses": ["UNKNOWN"] * MAX_SLOTS,
    "available_slots": 0,
    "temperature_c": None,
    "humidity_pct": None,
    "entry_distance_cm": None,
    "entry_detected": False,
    "last_update": 0,
}

lcd_override = {
    "line1": "",
    "line2": "",
    "until_ms": 0,
    "last_rendered": None,
}

auto_gate_close_deadline = None
previous_entry_detected = False
network_lock = None

if _thread is not None:
    try:
        network_lock = _thread.allocate_lock()
    except Exception:
        network_lock = None


def clamp_angle(angle):
    return max(0, min(180, int(angle)))


def angle_to_duty(angle):
    angle = clamp_angle(angle)
    return int(26 + (angle / 180) * 102)


def fit_lcd_text(text):
    text = str(text)
    if len(text) > LCD_COLS:
        return text[:LCD_COLS]
    return text + (" " * (LCD_COLS - len(text)))


def now_ms():
    return time.ticks_ms()


def initialize_hardware():
    if machine is None:
        return

    # Slot sensor pins must not overlap I2C pins used by LCD.
    for slot_pin in IR_SLOT_PINS[:MAX_SLOTS]:
        if slot_pin in (LCD_SDA_PIN, LCD_SCL_PIN):
            print("Config warning: IR slot pin {} conflicts with LCD I2C pin.".format(slot_pin))

    if hardware["servo"] is None:
        hardware["servo"] = machine.PWM(machine.Pin(SERVO_PIN), freq=SERVO_FREQ)
        hardware["servo"].duty(angle_to_duty(SERVO_CLOSE_ANGLE))

    if hardware["trig"] is None:
        hardware["trig"] = machine.Pin(ULTRASONIC_TRIG_PIN, machine.Pin.OUT)
        hardware["trig"].value(0)

    if hardware["echo"] is None:
        hardware["echo"] = machine.Pin(ULTRASONIC_ECHO_PIN, machine.Pin.IN)

    if not hardware["slot_pins"]:
        slot_mode = machine.Pin.PULL_UP if IR_SENSOR_USE_PULLUP else None
        hardware["slot_pins"] = []
        for pin in IR_SLOT_PINS[:MAX_SLOTS]:
            if slot_mode is None:
                hardware["slot_pins"].append(machine.Pin(pin, machine.Pin.IN))
            else:
                hardware["slot_pins"].append(machine.Pin(pin, machine.Pin.IN, slot_mode))

    if hardware["dht"] is None and dht is not None:
        hardware["dht"] = dht.DHT11(machine.Pin(DHT11_PIN))

    if hardware["tm1637"] is None:
        hardware["tm1637"] = TM1637(
            clk_pin=TM1637_CLK_PIN,
            dio_pin=TM1637_DIO_PIN,
            brightness=TM1637_BRIGHTNESS,
        )

    if hardware["lcd"] is None:
        i2c = machine.SoftI2C(
            sda=machine.Pin(LCD_SDA_PIN),
            scl=machine.Pin(LCD_SCL_PIN),
            freq=LCD_I2C_FREQ,
        )
        hardware["lcd"] = I2cLcd(i2c, LCD_I2C_ADDR, LCD_ROWS, LCD_COLS)
        set_lcd_override("System Booting", "Please wait...", LCD_EVENT_HOLD_MS)


def get_servo():
    initialize_hardware()
    return hardware["servo"]


def set_lcd_override(line1, line2, hold_ms=LCD_EVENT_HOLD_MS):
    lcd_override["line1"] = fit_lcd_text(line1)
    lcd_override["line2"] = fit_lcd_text(line2)
    lcd_override["until_ms"] = time.ticks_add(now_ms(), hold_ms)


def render_lcd(line1, line2):
    lcd = hardware["lcd"]
    if lcd is None:
        return

    current = (line1, line2)
    if lcd_override["last_rendered"] == current:
        return

    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(line1)
    lcd.move_to(0, 1)
    lcd.putstr(line2)
    lcd_override["last_rendered"] = current


def refresh_lcd():
    initialize_hardware()
    lcd = hardware["lcd"]
    if lcd is None:
        return

    live_line2 = fit_lcd_text("Slots:{} Gate:{}".format(state["available_slots"], state["gate_status"][0]))

    if time.ticks_diff(lcd_override["until_ms"], now_ms()) > 0:
        # Keep slot/gate line live so LCD stays in sync with TM1637 during temporary override banners.
        render_lcd(lcd_override["line1"], live_line2)
        return

    temp = state["temperature_c"]
    humidity = state["humidity_pct"]
    if temp is None or humidity is None:
        line1 = fit_lcd_text("Temp:--C H:--%")
    else:
        line1 = fit_lcd_text("Temp:{}C H:{}%".format(temp, humidity))

    render_lcd(line1, live_line2)


def refresh_tm1637():
    initialize_hardware()
    display = hardware["tm1637"]
    if display is None:
        return
    display.show_digit(state["available_slots"])


def read_ultrasonic_distance_cm():
    initialize_hardware()
    trig = hardware["trig"]
    echo = hardware["echo"]
    if trig is None or echo is None or machine is None:
        return None

    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    try:
        duration = machine.time_pulse_us(echo, 1, ULTRASONIC_TIMEOUT_US)
    except OSError:
        return None

    if duration < 0:
        return None

    return (duration * 0.0343) / 2


def read_slot_statuses():
    initialize_hardware()
    statuses = []
    for pin in hardware["slot_pins"]:
        pin_value = pin.value()
        if IR_SENSOR_ACTIVE_LOW:
            statuses.append("FULL" if pin_value == 0 else "OPEN")
        else:
            statuses.append("FULL" if pin_value == 1 else "OPEN")
    return statuses


def read_dht_state():
    initialize_hardware()
    sensor = hardware["dht"]
    if sensor is None:
        return None, None

    try:
        sensor.measure()
        return sensor.temperature(), sensor.humidity()
    except OSError:
        return None, None


def set_gate_position(target_angle, label, source):
    bounded_angle = clamp_angle(target_angle)
    servo_motor = get_servo()
    if servo_motor is None:
        print("Servo debug [{}]: hardware unavailable, requested {} at {} degrees".format(source, label, bounded_angle))
        state["gate_status"] = label
        state["gate_angle"] = bounded_angle
        return False

    servo_motor.duty(angle_to_duty(bounded_angle))
    state["gate_status"] = label
    state["gate_angle"] = bounded_angle
    print("Servo debug [{}]: {} gate to {} degrees".format(source, label.lower(), bounded_angle))
    set_lcd_override("Gate {}".format(label), "Src:{} {}deg".format(source[:6], bounded_angle))
    return True


def update_state_from_sensors():
    slot_statuses = read_slot_statuses()
    available_slots = 0
    for slot in slot_statuses:
        if slot == "OPEN":
            available_slots += 1

    temperature, humidity = read_dht_state()
    entry_distance = read_ultrasonic_distance_cm()
    entry_detected = entry_distance is not None and entry_distance <= ENTRY_DISTANCE_CM

    state["slot_statuses"] = slot_statuses
    state["available_slots"] = available_slots
    state["temperature_c"] = temperature
    state["humidity_pct"] = humidity
    state["entry_distance_cm"] = entry_distance
    state["entry_detected"] = entry_detected

    if available_slots == 0:
        state["system_status"] = "full"
    elif entry_detected:
        state["system_status"] = "vehicle_detected"
    elif state["gate_status"] == "OPEN":
        state["system_status"] = "gate_open"
    else:
        state["system_status"] = "idle"

    state["last_update"] = now_ms()


def handle_auto_gate_logic():
    global auto_gate_close_deadline, previous_entry_detected

    current_entry_detected = state["entry_detected"]
    rising_edge = current_entry_detected and not previous_entry_detected

    if rising_edge:
        if state["available_slots"] > 0:
            set_gate_position(SERVO_OPEN_ANGLE, "OPEN", "auto")
            auto_gate_close_deadline = time.ticks_add(now_ms(), AUTO_GATE_OPEN_MS)
        else:
            set_gate_position(SERVO_CLOSE_ANGLE, "CLOSED", "auto")
            set_lcd_override("Parking Full", "Gate remains shut")

    if auto_gate_close_deadline is not None and time.ticks_diff(now_ms(), auto_gate_close_deadline) >= 0:
        set_gate_position(SERVO_CLOSE_ANGLE, "CLOSED", "auto")
        auto_gate_close_deadline = None

    previous_entry_detected = current_entry_detected


def refresh_outputs():
    refresh_tm1637()
    refresh_lcd()


def get_system_output():
    """Return a controller snapshot for Telegram/Web/Blynk responses."""
    return {
        "service": state["service"],
        "system_status": state["system_status"],
        "gate_status": state["gate_status"],
        "gate_angle": state["gate_angle"],
        "relay_status": state["relay_status"],
        "slot_statuses": list(state["slot_statuses"]),
        "available_slots": state["available_slots"],
        "temp_c": state["temperature_c"],
        "humidity_pct": state["humidity_pct"],
        "entry_distance_cm": state["entry_distance_cm"],
        "entry_detected": state["entry_detected"],
        "last_update": state["last_update"],
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
                "gate_status": state["gate_status"],
                "servo_angle": state["gate_angle"],
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
                "gate_status": state["gate_status"],
                "servo_angle": state["gate_angle"],
            },
        }

    if command == "get_slots":
        return {
            "ok": True,
            "source": source,
            "command": command,
            "message": "{} slots available.".format(state["available_slots"]),
            "data": {
                "available_slots": state["available_slots"],
                "slots": list(state["slot_statuses"]),
            },
        }

    if command == "get_temp":
        return {
            "ok": True,
            "source": source,
            "command": command,
            "message": "Temperature {} C, humidity {} %.".format(
                state["temperature_c"],
                state["humidity_pct"],
            ),
            "data": {
                "temp_c": state["temperature_c"],
                "humidity_pct": state["humidity_pct"],
            },
        }

    if command == "light_on":
        return {
            "ok": True,
            "source": source,
            "command": command,
            "message": "Relay control is disabled for this build.",
            "data": {"relay_status": state["relay_status"]},
        }

    if command == "light_off":
        return {
            "ok": True,
            "source": source,
            "command": command,
            "message": "Relay control is disabled for this build.",
            "data": {"relay_status": state["relay_status"]},
        }

    return {
        "ok": False,
        "source": source,
        "command": command,
        "error": "unsupported_command",
        "data": {},
    }


def run_system_loop():
    initialize_hardware()
    update_state_from_sensors()
    refresh_outputs()

    while True:
        update_state_from_sensors()
        handle_auto_gate_logic()
        refresh_outputs()
        time.sleep_ms(CONTROL_LOOP_DELAY_MS)


def run():
    """Start enabled service loops and the shared controller loop."""
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
        print("No network services enabled. Running controller loop only.")
        run_system_loop()
        return

    if _thread is None:
        print("Threading unavailable; running controller loop only.")
        run_system_loop()
        return

    for service_name, service_runner in service_starters:
        print("Starting {} service...".format(service_name))
        _thread.start_new_thread(service_runner, ())

    print("Starting controller loop...")
    run_system_loop()


if __name__ == "__main__":
    run()
