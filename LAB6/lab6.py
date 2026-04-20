from machine import Pin, SPI, PWM
from mfrc522 import MFRC522
import sdcard
import os
import network
import urequests
import ntptime
import time


# =========================
# WiFi Configuration
# =========================
SSID = "Robotic WIFI"
PASSWORD = "rbtWIFI@2025"

# =========================
# Firestore Configuration
# =========================
PROJECT_ID = "iot-class-3f2b8"
FIRESTORE_URL = "https://firestore.googleapis.com/v1/projects/{}/databases/(default)/documents/attendance".format(PROJECT_ID)

# =========================
# Hardware Pin Configuration
# =========================
RFID_SCK  = 18
RFID_MOSI = 23
RFID_MISO = 19
RFID_RST  = 22
RFID_CS   = 16

SD_SCK    = 14
SD_MOSI   = 15
SD_MISO   = 2
SD_CS     = 13

BUZZER_PIN  = 4
BUZZER_FREQ = 1000

# =========================
# SD Card Log File
# =========================
LOG_FILE = "/sd/attendance.csv"

# =========================
# Student Database
# =========================
STUDENTS = {
    "2432192296203":  {"name": "Yubendh", "student_id": "2024251", "major": "Software Development"},
    "15820719118090": {"name": "Yubendh", "student_id": "2024251", "major": "Software Development"},
}

# =========================
# Hardware Setup
# =========================
rfid_spi = SPI(1, baudrate=1000000, polarity=0, phase=0,
               sck=Pin(RFID_SCK), mosi=Pin(RFID_MOSI), miso=Pin(RFID_MISO))
rdr = MFRC522(spi=rfid_spi, gpioRst=Pin(RFID_RST), gpioCs=Pin(RFID_CS))

sd_spi = SPI(2, baudrate=1000000,
             sck=Pin(SD_SCK), mosi=Pin(SD_MOSI), miso=Pin(SD_MISO))
sd_cs = Pin(SD_CS)

buzzer = PWM(Pin(BUZZER_PIN))
buzzer.freq(BUZZER_FREQ)
buzzer.duty(0)


def connect_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(False)
    time.sleep(0.5)
    wifi.active(True)
    if not wifi.isconnected():
        wifi.connect(SSID, PASSWORD)
        print("Connecting to WiFi", end="")
        while not wifi.isconnected():
            print(".", end="")
            time.sleep(0.3)
    print("\nWiFi connected:", wifi.ifconfig()[0])


def sync_time():
    try:
        ntptime.settime()
        print("Time synced via NTP")
    except Exception as e:
        print("NTP sync failed:", e)


UTC_OFFSET_HOURS = 7

def get_datetime_str():
    t = time.localtime(time.time() + UTC_OFFSET_HOURS * 3600)
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        t[0], t[1], t[2], t[3], t[4], t[5]
    )


def beep(duration):
    buzzer.duty(512)
    time.sleep(duration)
    buzzer.duty(0)


def save_to_sd(uid, name, student_id, major, datetime_str):
    sd = sdcard.SDCard(sd_spi, sd_cs)
    vfs = os.VfsFat(sd)
    os.mount(vfs, "/sd")

    try:
        try:
            os.stat(LOG_FILE)
            write_header = False
        except OSError:
            write_header = True

        with open(LOG_FILE, "a") as f:
            if write_header:
                f.write("UID,Name,StudentID,Major,DateTime\n")
            f.write("{},{},{},{},{}\n".format(uid, name, student_id, major, datetime_str))

        print("Saved to SD:", uid, name, datetime_str)
    except Exception as e:
        print("SD write error:", e)
    finally:
        os.umount("/sd")


def send_to_firestore(uid, name, student_id, major, datetime_str):
    data = {
        "fields": {
            "uid":        {"stringValue": uid},
            "name":       {"stringValue": name},
            "student_id": {"stringValue": student_id},
            "major":      {"stringValue": major},
            "datetime":   {"stringValue": datetime_str},
        }
    }
    try:
        res = urequests.post(FIRESTORE_URL, json=data)
        print("Firestore:", res.text)
        res.close()
    except Exception as e:
        print("Firestore error:", e)


def main():
    connect_wifi()
    sync_time()

    print("Scan RFID card...")

    while True:
        (stat, tag_type) = rdr.request(rdr.REQIDL)

        if stat == rdr.OK:
            (stat, uid) = rdr.anticoll()

            if stat == rdr.OK:
                uid_str = "".join([str(b) for b in uid])
                print("UID:", uid_str)

                datetime_str = get_datetime_str()

                if uid_str in STUDENTS:
                    student    = STUDENTS[uid_str]
                    name       = student["name"]
                    student_id = student["student_id"]
                    major      = student["major"]

                    print("Valid:", name, student_id, major)
                    print("DateTime:", datetime_str)

                    beep(0.3)
                    save_to_sd(uid_str, name, student_id, major, datetime_str)
                    send_to_firestore(uid_str, name, student_id, major, datetime_str)

                else:
                    print("Unknown Card")
                    beep(3)

                time.sleep(2)


main()
