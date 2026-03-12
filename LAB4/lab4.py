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

# ---------------- I2C SENSORS ----------------
# Shared bus for BMP280 + DS3231 on GPIO22 / GPIO21
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
print("I2C devices (bus0):", [hex(addr) for addr in i2c.scan()])

# Dedicated bus for MLX90614 on GPIO16 (SCL) / GPIO17 (SDA)
i2c_mlx = I2C(1, scl=Pin(16), sda=Pin(17), freq=50000)
print("I2C devices (mlx bus):", [hex(addr) for addr in i2c_mlx.scan()])

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
        mlx = MLX90614(i2c_mlx)
    except Exception:
        mlx = None

# ---------------- FEVER LOGIC CONFIG ----------------
FEVER_TEMP_C = 37.5
BODY_TEMP_MIN_C = 30.0
BODY_TEMP_MAX_C = 45.0
MLX_READ_RETRIES = 3
MLX_I2C_ADDR = 0x5A
BOOT_TEMP_SAMPLE_COUNT = 5
BOOT_TEMP_MAX_SPREAD_C = 2.0

readings = []


def read_body_temp_c():
    if mlx is None:
        return None

    for _ in range(MLX_READ_RETRIES):
        try:
            temp = float(mlx.read_object_temp())
            if BODY_TEMP_MIN_C <= temp <= BODY_TEMP_MAX_C:
                return temp
        except Exception:
            pass
        time.sleep_ms(50)

    return None


def check_mlx_on_boot():
    print("MLX90614 boot check...")

    devices = i2c_mlx.scan()
    if MLX_I2C_ADDR not in devices:
        print("MLX90614: FAIL - address 0x5a not found on I2C bus")
        return False

    if mlx is None:
        print("MLX90614: FAIL - driver init failed")
        return False

    samples = []
    for _ in range(BOOT_TEMP_SAMPLE_COUNT):
        try:
            t = float(mlx.read_object_temp())
            if BODY_TEMP_MIN_C <= t <= BODY_TEMP_MAX_C:
                samples.append(t)
        except Exception:
            pass
        time.sleep_ms(100)

    if len(samples) < 3:
        print("MLX90614: FAIL - not enough valid samples:", samples)
        return False

    spread = max(samples) - min(samples)
    if spread > BOOT_TEMP_MAX_SPREAD_C:
        print("MLX90614: FAIL - unstable samples:", samples)
        return False

    avg = sum(samples) / len(samples)
    print("MLX90614: PASS - stable reading {:.2f}C, samples={}".format(avg, samples))
    return True


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


mlx_ok = check_mlx_on_boot()

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
    body_temp = read_body_temp_c() if mlx_ok else None
    fever_flag = 1 if (body_temp is not None and body_temp >= FEVER_TEMP_C) else 0

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
