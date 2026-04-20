LAB 6: Smart RFID System with Cloud &
SD Logging
1. Overview
In this lab, students will design and implement a smart RFID-based attendance system using
ESP32 and MicroPython (Thonny). The system integrates RFID-RC522, SD card, Firestore,
and a buzzer. The system identifies users, logs attendance locally and remotely, and
provides real-time feedback.
2. Learning Outcomes (CLO Alignment)
• Integrate SPI-based RFID sensor (RC522) with ESP32
• Implement UID-based identification system
• Design structured data storage (CSV format)
• Store data locally (SD card) and remotely (Firestore)
• Implement real-time feedback using buzzer
• Apply system integration across multiple modules
3. Connection
4. Task
1. Read UID from RFID card
- Detect card and retrieve its unique ID (UID)
2. Match UID with student database
- Compare UID with predefined data
- If found ->valid student
- If not -> unknown card
3. Generate current datetime
- Format:
YYYY-MM-DD HH:MM:SS
4. If UID is valid:
- Activate buzzer for 0.3 seconds
- Save data to SD card (CSV format):
UID, Name, StudentID, Major, DateTime
- Send data to Firestore
5. If UID is invalid:
- Activate buzzer for 3 seconds
- Display: "Unknown Card"
- Do not save or send data