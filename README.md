# Smart IoT Parking Management System (Mini Project)

Small, modular firmware structure for ESP32 + MicroPython.

## Simplified Layout

- `firmware/main.py`: central controller containing core functions and system outputs.
- `firmware/boot.py`: early boot stage.
- `firmware/config.py`: small quick-edit config file for fast setting updates.
- `firmware/hardware/sensors.py`: ultrasonic, IR slots, DHT11 responsibilities.
- `firmware/hardware/actuators.py`: servo gate and relay lighting responsibilities.
- `firmware/hardware/displays.py`: TM1637 and LCD I2C display responsibilities.
- `firmware/services/webserver_service.py`: consumes outputs from `main.py` and sends dashboard requests back to `main.py`.
- `firmware/services/telegram_service.py`: consumes outputs from `main.py` and sends bot requests back to `main.py`.
- `firmware/services/blynk_service.py`: consumes outputs from `main.py` and sends app requests back to `main.py`.
- `firmware/storage/runtime_state.json`: persisted mini runtime state.
