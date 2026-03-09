from machine import ADC, Pin, I2C
import time
import network
import urequests

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
SSID = "AUPP Wifi"

# Node-RED endpoint
NODE_RED_URL = "http://10.10.62.226:1880/gas"

# connect wifi
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID)

print("Connecting to WiFi...")

while not wifi.isconnected():
    time.sleep(1)

print("Connected:", wifi.ifconfig())


# ---------------- GAS SENSOR ----------------
gas_sensor = ADC(Pin(33))
gas_sensor.atten(ADC.ATTN_11DB)

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
    except Exception:
        rtc = None

mlx = None
if MLX90614 is not None:
    try:
        mlx = MLX90614(i2c)
    except Exception:
        mlx = None

readings = []


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
        # BMP280 driver returns pressure in Pa.
        return float(bmp280.pressure) / 100.0
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

    # read sensor
    raw_value = gas_sensor.read()
    readings.append(raw_value)

    # keep last 5 readings
    if len(readings) > 5:
        readings.pop(0)

    # calculate average
    gas_avg = sum(readings) / len(readings)

    print("Raw:", raw_value, "Average:", gas_avg)

    # ---------------- TASK 2 : RISK CLASSIFICATION ----------------
    if gas_avg < 2100:
        risk_level = "SAFE"
    elif gas_avg < 2600:
        risk_level = "WARNING"
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

    # prepare data packet
    data = {
        "gas_avg": gas_avg,
        "risk_level": risk_level,
        "body_temp": body_temp,
        "fever_flag": fever_flag,
        "pressure_hpa": pressure_hpa,
        "altitude_m": altitude_m,
        "ds3231_timestamp": ds3231_timestamp,
    }

    # send to Node-RED
    try:
        response = urequests.post(NODE_RED_URL, json=data)
        response.close()
        print("Data sent:", data)

    except:
        print("Send failed")

    print("------------------------")

    time.sleep(5)
