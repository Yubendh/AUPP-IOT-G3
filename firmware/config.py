# Quick config: small centralized settings file for fast edits without navigating multiple modules.

# On-device smoke-test settings.
TEST_SAMPLE_COUNT = 10
TEST_SAMPLE_DELAY_MS = 200

# Wi-Fi quick settings.
WIFI_SSID = "AUPP Wifi"
WIFI_PASSWORD = ""
WIFI_CONNECT_RETRIES = 15

# System timing settings.
CONTROL_LOOP_DELAY_MS = 200
AUTO_GATE_OPEN_MS = 3000
LCD_EVENT_HOLD_MS = 2500
ENTRY_DISTANCE_CM = 10

# Servo quick settings.
SERVO_PIN = 13
SERVO_FREQ = 50
SERVO_OPEN_ANGLE = 90
SERVO_CLOSE_ANGLE = 0

# Ultrasonic quick settings.
ULTRASONIC_TRIG_PIN = 27
ULTRASONIC_ECHO_PIN = 26
ULTRASONIC_TIMEOUT_US = 30000

# Parking slot quick settings.
MAX_SLOTS = 4
IR_SLOT_PINS = (12, 14, 18, 19)

# DHT11 quick settings.
DHT11_PIN = 33

# TM1637 quick settings.
TM1637_CLK_PIN = 17
TM1637_DIO_PIN = 16
TM1637_BRIGHTNESS = 5

# LCD quick settings.
LCD_I2C_ADDR = 0x27
LCD_SDA_PIN = 21
LCD_SCL_PIN = 22
LCD_ROWS = 2
LCD_COLS = 16
LCD_I2C_FREQ = 400000

# Telegram quick settings.
TELEGRAM_BOT_TOKEN = "8317214199:AAFkZlexTEuNOvYYAT_mcNOeSshu2Ro0P_k"
TELEGRAM_CHAT_ID = "-1003317505805"
TELEGRAM_POLL_SECONDS = 2

# Blynk quick settings.
BLYNK_AUTH_TOKEN = "r0Wei7vXhxaAxySVu9Ud4P-i_8Ds3FLh"
BLYNK_BASE_URL = "http://blynk.cloud/external/api"
BLYNK_POLL_SECONDS = 2
BLYNK_SERVO_VPIN = "V0"
BLYNK_SLOTS_VPIN = "V1"
BLYNK_TEMPERATURE_VPIN = "V2"

# Web server quick settings.
WEBSERVER_HOST = "0.0.0.0"
WEBSERVER_PORT = 80
WEBSERVER_BACKLOG = 5

# Startup toggles.
ENABLE_BLYNK_SERVICE = True
ENABLE_TELEGRAM_SERVICE = True
ENABLE_WEBSERVER_SERVICE = True
