"""Project configuration for ESP32 smart parking system."""

# ---- I2C (LCD) ----
I2C_SDA_PIN = 21
I2C_SCL_PIN = 22
I2C_FREQ = 400000
LCD_I2C_ADDR = 0x27
LCD_LINES = 2
LCD_COLS = 16

# ---- Servo gate ----
SERVO_PIN = 13
SERVO_OPEN_ANGLE = 90
SERVO_CLOSED_ANGLE = 0
SERVO_FREQ = 50
GATE_OPEN_SECONDS = 3

# ---- Ultrasonic ----
ULTRASONIC_TRIG_PIN = 27
ULTRASONIC_ECHO_PIN = 26
CAR_DETECT_DISTANCE_CM = 12
ULTRASONIC_TIMEOUT_US = 30000

# ---- DHT11 ----
DHT11_PIN = 4
DHT_READ_INTERVAL_MS = 5000

# ---- TM1637 4-digit ----
TM1637_CLK_PIN = 18
TM1637_DIO_PIN = 19
TM1637_BRIGHTNESS = 4  # 0-7

# ---- Parking slots (5 IR sensors) ----
# Active-low IR modules are common: 0 = occupied, 1 = free.
IR_ACTIVE_LOW = True
IR_SLOT_PINS = [32, 33, 25, 14, 12]

# ---- Loop tuning ----
MAIN_LOOP_DELAY_MS = 150
TRIGGER_COOLDOWN_MS = 2500