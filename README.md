# IOT Smart Parking Mini-Project

# Introduction

The project aims to simulate a real parking lot, but with different sensors and smart features implemented for a more modern take on how parking lots should be managed.

Everything is fully automated with multiple dashboards and UIs to control things like closing and opening of doors and viewing status/outputs of various sensors.

# Hardware Description

## Telegram Bridge

If Telegram is too heavy to run directly on the ESP32, run the bot on your computer and let it call the ESP32 over local Wi-Fi.

ESP32 local endpoints:
- `/api/status`
- `/api/open`
- `/api/close`
- `/api/slots`
- `/api/temp`

Computer bridge script:
- [tools/telegram_bridge.py](/abs/path/c:/Users/User/Documents/iot parking branch/AUPP-IOT-G3/tools/telegram_bridge.py)

Example setup on your computer:

```powershell
$env:TELEGRAM_BOT_TOKEN="your_bot_token"
$env:TELEGRAM_CHAT_ID="your_chat_id"
$env:ESP32_BASE_URL="http://192.168.1.50"
python tools/telegram_bridge.py
```

The computer and ESP32 should be connected to the same Wi-Fi network.
