from machine import ADC, Pin, I2C
import time
import network
import urequests
import ntptime

try:
    from bmp280 import BMP280
except ImportError:
    BMP280 = None
try:
    from ds3231 import DS3231
except ImportError:
    DS3231 = None
try:
    from mlx90614 import MLX90614
except ImportError:
    MLX90614 = None

# ---------------- WIFI ----------------

WIFI_SSID = "Lythea"
WIFI_PASS = "34494271"
NODE_RED_URL = "http://192.168.0.104:1880/gas"

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASS)
print("Connecting to WiFi...")
while not wifi.isconnected():
    time.sleep(1)
print("Connected:", wifi.ifconfig())

try:
    ntptime.settime()
    utc = time.time()
    t = time.localtime(utc + 7 * 3600)  # UTC+7
    print("NTP synced (UTC+7):", t)
except Exception as e:
    print("NTP sync failed:", e)
    t = None

# ---------------- GAS SENSOR ----------------
gas_sensor = ADC(Pin(33))
gas_sensor.atten(ADC.ATTN_11DB)
gas_sensor.width(ADC.WIDTH_12BIT)

readings = []
raw_history = []
avg_history = []

# ---------------- I2C SENSORS (SHARED BUS) ----------------
# BMP280 + DS3231 + MLX90614 all on GPIO22 / GPIO21

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)

bmp280 = None
if BMP280 is not None:
    try:
        bmp280 = BMP280(i2c=i2c)
    except Exception:
        bmp280 = None

rtc = None
if DS3231 is not None:
    try:
        rtc = DS3231(i2c)
        if t is not None:
            rtc.set_time(t[0], t[1], t[2], t[3], t[4], t[5])
    except Exception:
        rtc = None

mlx = None
if MLX90614 is not None:
    try:
        mlx = MLX90614(i2c)
    except Exception:
        mlx = None


def read_body_temp_c():
    if mlx is None:
        return None
    try:
        return float(mlx.read_object_temp())
    except Exception:
        return None

def read_pressure_hpa():
    if bmp280 is None:
        return None
    try:
        return float(bmp280.pressure) / 100.0  # BMP280 driver returns pressure in Pa.
    except Exception:
        return None

def read_altitude_m():
    if bmp280 is None:
        return None
    try:
        return float(bmp280.altitude)
    except Exception:
        return None

def read_ds3231_timestamp():
    if rtc is None:
        return None
    try:
        dt = rtc.get_time()
    except Exception:
        return None
    if not dt or len(dt) < 6:
        return None
    year, month, day, hour, minute, second = dt[:6]
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        year, month, day, hour, minute, second
    )


# ---------------- MAIN LOOP ----------------

while True:
    raw_value = gas_sensor.read()
    readings.append(raw_value)

    if len(readings) > 5:
        readings.pop(0)

    gas_avg = sum(readings) / len(readings)

    raw_history.append(raw_value)
    avg_history.append(round(gas_avg, 1))
    if len(raw_history) > 5:
        raw_history.pop(0)
    if len(avg_history) > 5:
        avg_history.pop(0)

    print("Raw:", raw_value, "| Average:", gas_avg)

    if len(readings) == 5:
        print("Last 5 raw:", raw_history)
        print("Last 5 avg:", avg_history)

# ---------------- TASK 2 : RISK CLASSIFICATION ----------------
    if gas_avg < 690:
        risk_level = "SAFE"
    elif gas_avg < 691:
        risk_level = "WARNING" # change threshold so it's easier to test
    else:
        risk_level = "DANGER"
    print("Risk Level:", risk_level)

# ---------------- TASK 3 : FEVER DETECTION ----------------
    body_temp = read_body_temp_c()
    fever_flag = 1 if (body_temp is not None and body_temp >= 32.5) else 0
    print("Body Temp:", body_temp, "C | Fever Flag:", fever_flag)

# ---------------- TASK 4 : PRESSURE & ALTITUDE ----------------
    pressure_hpa = read_pressure_hpa()
    altitude_m = read_altitude_m()
    ds3231_timestamp = read_ds3231_timestamp()
    print("Pressure (hPa):", pressure_hpa)
    print("Altitude (m):", altitude_m)
    print("DS3231 Time:", ds3231_timestamp)

    data = {
        "gas_avg": gas_avg,
        "risk_level": risk_level,
        "body_temp": body_temp,
        "fever_flag": fever_flag,
        "pressure_hpa": pressure_hpa,
        "altitude_m": altitude_m,
        "ds3231_timestamp": ds3231_timestamp,
    }

    try:
        response = urequests.post(NODE_RED_URL, json=data)
        response.close()
        print("Data sent:", data)
    except:
        print("Send failed")

    print("------------------------")
    time.sleep(5)
