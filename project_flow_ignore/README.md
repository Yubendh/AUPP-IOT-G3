# ESP32 Smart Parking (MicroPython)

This project implements your parking flow:

1. Ultrasonic detects incoming car.
2. System checks real-time slot availability from 5 IR sensors.
3. If slot available: TM1637 shows count, gate opens (servo), then closes.
4. If no slot: TM1637 shows `FULL`, gate stays closed.
5. LCD shows slots + system status / DHT11 temperature & humidity.

## Files

- `main.py` : Main parking loop and control logic.
- `config.py` : Pin map and behavior settings.
- `tm1637.py` : TM1637 display driver.
- `lcd_api.py`, `machine_i2c_lcd.py` : LCD I2C driver.

## Default Pin Mapping (ESP32)

- LCD I2C: SDA=`21`, SCL=`22`, addr=`0x27`
- Servo: `13`
- Ultrasonic: TRIG=`27`, ECHO=`26`
- DHT11: `4`
- TM1637: CLK=`18`, DIO=`19`
- IR slots (5): `[32, 33, 25, 14, 12]`

Change pins in `config.py` if your wiring is different.

## Run

1. Copy all files in this folder to ESP32.
2. Ensure MicroPython firmware is installed on ESP32.
3. Run `main.py` (or rename to `boot.py` / `main.py` on board startup).

## Notes

- IR sensors are configured as active-low (`0` = occupied). Change `IR_ACTIVE_LOW` in `config.py` if needed.
- If your servo direction is reversed, swap `SERVO_OPEN_ANGLE` and `SERVO_CLOSED_ANGLE` in `config.py`.
- TM1637 shows slot number when available, and `FULL` when no slot remains.