# Quick config: small centralized settings file for fast edits without navigating multiple modules.

# On-device smoke-test settings.
TEST_SAMPLE_COUNT = 10
TEST_SAMPLE_DELAY_MS = 200

# Wi-Fi quick settings.
WIFI_SSID = "AUPP Wifi"
WIFI_PASSWORD = ""
WIFI_CONNECT_RETRIES = 15

# Servo quick settings.
SERVO_PIN = 13
SERVO_FREQ = 50
SERVO_OPEN_ANGLE = 90
SERVO_CLOSE_ANGLE = 0

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
