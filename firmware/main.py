"""Main controller: shared hardware state and command routing for all services."""

import sys
import time
import gc

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
    IR_DEBUG_ENABLED,
    IR_DEBUG_INTERVAL_MS,
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
    ULTRASONIC_MAX_DETECTION_CM,
    ULTRASONIC_SECOND_ECHO_PIN,
    ULTRASONIC_SECOND_ENABLED,
    ULTRASONIC_SECOND_TRIG_PIN,
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
    "trig2": None,
    "echo2": None,
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
    "entry_distance_cm_secondary": None,
    "entry_detected": False,
    "active_entry_sensor": None,
    "last_update": 0,
}

lcd_override = {
    "line1": "",
    "line2": "",
    "until_ms": 0,
    "last_rendered": None,
}

auto_gate_close_deadline = None
last_ir_debug_ms = None
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

    if ULTRASONIC_SECOND_ENABLED:
        if hardware["trig2"] is None:
            hardware["trig2"] = machine.Pin(ULTRASONIC_SECOND_TRIG_PIN, machine.Pin.OUT)
            hardware["trig2"].value(0)
        if hardware["echo2"] is None:
            if ULTRASONIC_SECOND_ECHO_PIN == ULTRASONIC_SECOND_TRIG_PIN:
                hardware["echo2"] = hardware["trig2"]
            else:
                hardware["echo2"] = machine.Pin(ULTRASONIC_SECOND_ECHO_PIN, machine.Pin.IN)

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

    distance_cm = (duration * 0.0343) / 2
    if distance_cm > ULTRASONIC_MAX_DETECTION_CM:
        return None
    return distance_cm


def read_ultrasonic_distance_cm_second():
    initialize_hardware()
    trig = hardware["trig2"]
    echo = hardware["echo2"]
    if trig is None or echo is None or machine is None or not ULTRASONIC_SECOND_ENABLED:
        return None

    # Support one-pin mode when TRIG/ECHO share the same GPIO.
    if ULTRASONIC_SECOND_TRIG_PIN == ULTRASONIC_SECOND_ECHO_PIN:
        try:
            trig.init(machine.Pin.OUT)
            trig.value(0)
            time.sleep_us(2)
            trig.value(1)
            time.sleep_us(10)
            trig.value(0)
            trig.init(machine.Pin.IN)
            duration = machine.time_pulse_us(trig, 1, ULTRASONIC_TIMEOUT_US)
            trig.init(machine.Pin.OUT)
            trig.value(0)
        except OSError:
            return None
    else:
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

    distance_cm = (duration * 0.0343) / 2
    if distance_cm > ULTRASONIC_MAX_DETECTION_CM:
        return None
    return distance_cm


def get_detected_sensor(primary_detected, secondary_detected):
    active_sensor = state["active_entry_sensor"]

    # Hold ownership on the current sensor until it clears so the servo
    # only responds to one ultrasonic source at a time.
    if active_sensor == "primary":
        if primary_detected:
            return "primary"
        if secondary_detected:
            return "secondary"
        return None

    if active_sensor == "secondary":
        if secondary_detected:
            return "secondary"
        if primary_detected:
            return "primary"
        return None

    if primary_detected:
        return "primary"
    if secondary_detected:
        return "secondary"
    return None


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


def maybe_log_ir_debug():
    global last_ir_debug_ms

    if not IR_DEBUG_ENABLED:
        return

    current_ms = now_ms()
    if (
        last_ir_debug_ms is not None
        and time.ticks_diff(current_ms, last_ir_debug_ms) < IR_DEBUG_INTERVAL_MS
    ):
        return

    last_ir_debug_ms = current_ms
    sensor_parts = []
    for index, pin in enumerate(hardware["slot_pins"], 1):
        raw_value = pin.value()
        if IR_SENSOR_ACTIVE_LOW:
            state_label = "DETECTED" if raw_value == 0 else "CLEAR"
        else:
            state_label = "DETECTED" if raw_value == 1 else "CLEAR"
        sensor_parts.append("IR{} raw={} state={}".format(index, raw_value, state_label))

    if state["entry_distance_cm"] is None:
        sensor_parts.append("US1=none")
    else:
        sensor_parts.append("US1={:.1f}cm".format(state["entry_distance_cm"]))

    if state["entry_distance_cm_secondary"] is None:
        sensor_parts.append("US2=none")
    else:
        sensor_parts.append("US2={:.1f}cm".format(state["entry_distance_cm_secondary"]))
    sensor_parts.append("ENTRY={}".format("yes" if state["entry_detected"] else "no"))
    sensor_parts.append("ACTIVE={}".format(state["active_entry_sensor"] or "none"))
    sensor_parts.append("SLOTS={}".format(state["available_slots"]))
    sensor_parts.append("GATE={}".format(state["gate_status"]))

    print("Sensor debug [{}]".format(" | ".join(sensor_parts)))


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
        state["gate_status"] = label
        state["gate_angle"] = bounded_angle
        return False

    servo_motor.duty(angle_to_duty(bounded_angle))
    state["gate_status"] = label
    state["gate_angle"] = bounded_angle
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
    entry_distance_secondary = read_ultrasonic_distance_cm_second()
    primary_detected = entry_distance is not None and entry_distance <= ENTRY_DISTANCE_CM
    secondary_detected = (
        entry_distance_secondary is not None and entry_distance_secondary <= ENTRY_DISTANCE_CM
    )
    active_entry_sensor = get_detected_sensor(primary_detected, secondary_detected)
    entry_detected = active_entry_sensor is not None

    state["slot_statuses"] = slot_statuses
    state["available_slots"] = available_slots
    state["temperature_c"] = temperature
    state["humidity_pct"] = humidity
    state["entry_distance_cm"] = entry_distance
    state["entry_distance_cm_secondary"] = entry_distance_secondary
    state["entry_detected"] = entry_detected
    state["active_entry_sensor"] = active_entry_sensor

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
    global auto_gate_close_deadline

    current_entry_detected = state["entry_detected"]

    if current_entry_detected:
        if state["available_slots"] > 0:
            if state["gate_status"] != "OPEN":
                set_gate_position(SERVO_OPEN_ANGLE, "OPEN", "auto")
            auto_gate_close_deadline = time.ticks_add(now_ms(), AUTO_GATE_OPEN_MS)
        else:
            if state["gate_status"] != "CLOSED":
                set_gate_position(SERVO_CLOSE_ANGLE, "CLOSED", "auto")
            auto_gate_close_deadline = None
            set_lcd_override("Parking Full", "Gate remains shut")

    if (
        not current_entry_detected
        and auto_gate_close_deadline is not None
        and time.ticks_diff(now_ms(), auto_gate_close_deadline) >= 0
    ):
        set_gate_position(SERVO_CLOSE_ANGLE, "CLOSED", "auto")
        auto_gate_close_deadline = None


def refresh_outputs():
    maybe_log_ir_debug()
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
        "entry_distance_cm_secondary": state["entry_distance_cm_secondary"],
        "entry_detected": state["entry_detected"],
        "active_entry_sensor": state["active_entry_sensor"],
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
    service_specs = []

    # Start Telegram first so its TLS session has the best chance of fitting
    # on low-memory boards before other network services are imported.
    if ENABLE_TELEGRAM_SERVICE:
        service_specs.append(("telegram", "telegram_service", "run_bot_loop"))

    if ENABLE_BLYNK_SERVICE:
        service_specs.append(("blynk", "blynk_service", "run_blynk_loop"))

    if ENABLE_WEBSERVER_SERVICE:
        service_specs.append(("webserver", "webserver_service", "run_webserver_loop"))

    if not service_specs:
        print("No network services enabled. Running controller loop only.")
        run_system_loop()
        return

    if _thread is None:
        print("Threading unavailable; running controller loop only.")
        run_system_loop()
        return

    def start_service_thread(module_name, runner_name):
        try:
            try:
                module = __import__("services." + module_name, None, None, (runner_name,))
            except ImportError:
                module = __import__(module_name, None, None, (runner_name,))
            getattr(module, runner_name)()
        except Exception as exc:
            print("Service bootstrap error [{}]:".format(module_name), exc)
            try:
                sys.print_exception(exc)
            except Exception:
                pass

    def initialize_telegram_service():
        try:
            try:
                module = __import__("services.telegram_service", None, None, ("initialize_update_cursor",))
            except ImportError:
                module = __import__("telegram_service", None, None, ("initialize_update_cursor",))

            initializer = getattr(module, "initialize_update_cursor", None)
            if initializer is None:
                return True

            for _ in range(3):
                gc.collect()
                if initializer():
                    return True
                time.sleep_ms(500)
            return False
        except Exception as exc:
            print("Telegram pre-init error:", exc)
            try:
                sys.print_exception(exc)
            except Exception:
                pass
            return False

    for service_name, module_name, runner_name in service_specs:
        print("Starting {} service...".format(service_name))
        gc.collect()
        if service_name == "telegram" and not initialize_telegram_service():
            print("Telegram pre-init failed; starting loop anyway.")
        _thread.start_new_thread(start_service_thread, (module_name, runner_name))
        time.sleep_ms(250)
        gc.collect()

    print("Starting controller loop...")
    run_system_loop()


if __name__ == "__main__":
    run()
