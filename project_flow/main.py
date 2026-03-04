from machine import Pin, PWM, SoftI2C, time_pulse_us
import time
import dht

import config
from machine_i2c_lcd import I2cLcd
from tm1637 import TM1637


class GateController:
    def __init__(self, pin, freq=50, closed_angle=0, open_angle=90):
        self.closed_angle = closed_angle
        self.open_angle = open_angle
        self.pwm = PWM(Pin(pin), freq=freq)
        self.set_angle(self.closed_angle)

    def _angle_to_duty(self, angle):
        min_duty = 26
        max_duty = 128
        return int(min_duty + (max_duty - min_duty) * angle / 180)

    def set_angle(self, angle):
        self.pwm.duty(self._angle_to_duty(angle))

    def open_gate(self):
        self.set_angle(self.open_angle)

    def close_gate(self):
        self.set_angle(self.closed_angle)


class ParkingSystem:
    def __init__(self):
        self.trig = Pin(config.ULTRASONIC_TRIG_PIN, Pin.OUT)
        self.echo = Pin(config.ULTRASONIC_ECHO_PIN, Pin.IN)
        self.ir_pins = [Pin(pin_no, Pin.IN, Pin.PULL_UP) for pin_no in config.IR_SLOT_PINS]
        self.dht11 = dht.DHT11(Pin(config.DHT11_PIN))

        i2c = SoftI2C(
            sda=Pin(config.I2C_SDA_PIN),
            scl=Pin(config.I2C_SCL_PIN),
            freq=config.I2C_FREQ,
        )
        self.lcd = I2cLcd(i2c, config.LCD_I2C_ADDR, config.LCD_LINES, config.LCD_COLS)
        self.tm = TM1637(config.TM1637_CLK_PIN, config.TM1637_DIO_PIN, config.TM1637_BRIGHTNESS)
        self.gate = GateController(
            config.SERVO_PIN,
            config.SERVO_FREQ,
            config.SERVO_CLOSED_ANGLE,
            config.SERVO_OPEN_ANGLE,
        )

        self.last_dht_ms = 0
        self.last_trigger_ms = 0
        self.last_status = "System Booting"
        self.last_temp = None
        self.last_hum = None

    def ultrasonic_distance_cm(self):
        self.trig.value(0)
        time.sleep_us(2)
        self.trig.value(1)
        time.sleep_us(10)
        self.trig.value(0)

        duration = time_pulse_us(self.echo, 1, config.ULTRASONIC_TIMEOUT_US)
        if duration < 0:
            return None

        return (duration * 0.0343) / 2

    def slot_occupied(self, pin_obj):
        value = pin_obj.value()
        if config.IR_ACTIVE_LOW:
            return value == 0
        return value == 1

    def get_available_slots(self):
        occupied_count = 0
        for pin_obj in self.ir_pins:
            if self.slot_occupied(pin_obj):
                occupied_count += 1
        return len(self.ir_pins) - occupied_count

    def update_tm1637(self, available_slots):
        if available_slots <= 0:
            self.tm.show_full()
        else:
            self.tm.show_number(available_slots)

    def update_dht(self):
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_dht_ms) < config.DHT_READ_INTERVAL_MS:
            return

        self.last_dht_ms = now
        try:
            self.dht11.measure()
            self.last_temp = self.dht11.temperature()
            self.last_hum = self.dht11.humidity()
        except Exception:
            self.last_temp = None
            self.last_hum = None

    def update_lcd(self, available_slots):
        line1 = "Slots:{}/{}".format(available_slots, len(self.ir_pins))

        if self.last_temp is None or self.last_hum is None:
            line2 = self.last_status[:16]
        else:
            line2 = "T:{}C H:{}%".format(self.last_temp, self.last_hum)

        self.lcd.clear()
        self.lcd.move_to(0, 0)
        self.lcd.putstr(line1[:16])
        self.lcd.move_to(0, 1)
        self.lcd.putstr(line2[:16])

    def handle_vehicle_trigger(self, available_slots):
        distance = self.ultrasonic_distance_cm()
        if distance is None:
            return

        if distance > config.CAR_DETECT_DISTANCE_CM:
            return

        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_trigger_ms) < config.TRIGGER_COOLDOWN_MS:
            return

        self.last_trigger_ms = now

        if available_slots > 0:
            self.last_status = "Slot available"
            self.gate.open_gate()
            time.sleep(config.GATE_OPEN_SECONDS)
            self.gate.close_gate()
            self.last_status = "Gate closed"
        else:
            self.last_status = "No slot"

    def run(self):
        self.last_status = "System Ready"
        self.gate.close_gate()

        while True:
            available_slots = self.get_available_slots()
            self.update_tm1637(available_slots)

            self.handle_vehicle_trigger(available_slots)

            self.update_dht()
            self.update_lcd(available_slots)

            time.sleep_ms(config.MAIN_LOOP_DELAY_MS)


system = ParkingSystem()
system.run()