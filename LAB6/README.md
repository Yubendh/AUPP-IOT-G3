# LAB 6: Smart RFID System with Cloud & SD Logging
# Team memebers: 
- Lim Houykea
- Deth Sokunboranich
- Meouk Sovannarith
- Vanthan Buth Yubendh

## Tasks:

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

-Evidences of above tasks are shown in DEMO video below.

## DEMO VIDEO

https://youtu.be/JEeHcsOtwK4

## System Flowchart

![flowchart](system_flowchart.png)

## CSV file for database

LAB6/sdcard.csv

## Firestore screenshot

![Firestore](firestore.jpeg)





