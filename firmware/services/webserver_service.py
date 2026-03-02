# Web server service: presents main controller outputs on dashboard endpoints and sends user-triggered requests to main controller actions.

import network
import socket
import machine
import dht
import time

# =========================
# WIFI CONFIG
# =========================
ssid = "YOUR_WIFI_NAME"
password = "YOUR_WIFI_PASSWORD"

# =========================
# HARDWARE SETUP
# =========================
servo = machine.PWM(machine.Pin(14), freq=50)
relay = machine.Pin(26, machine.Pin.OUT)
dht_sensor = dht.DHT11(machine.Pin(4))

# =========================
# SYSTEM VARIABLES
# =========================
gate_status = "CLOSED"
relay_status = "OFF"

slot1 = "FULL"
slot2 = "OPEN"
slot3 = "FULL"
slot4 = "FULL"
slot5 = "FULL"

# =========================
# WIFI CONNECTION
# =========================
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(ssid, password)

print("Connecting to WiFi...")
while not wifi.isconnected():
    pass

print("Connected!")
print("IP Address:", wifi.ifconfig()[0])

# =========================
# SERVO FUNCTIONS
# =========================
def open_gate():
    global gate_status
    servo.duty(115)
    gate_status = "OPEN"

def close_gate():
    global gate_status
    servo.duty(40)
    gate_status = "CLOSED"

# =========================
# HTML PAGE
# =========================
def webpage(temp):

    slots = [slot1, slot2, slot3, slot4, slot5]
    available = 0
    for s in slots:
        if s == "OPEN":
            available += 1

    def slot_class(status):
        if status == "OPEN":
            return "slot open"
        return "slot full"

    return f"""<!DOCTYPE html>
<html>
<head>
<title>Smart Parking</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="5">

<style>
body {{
    margin:0;
    font-family:Arial;
    background:#1E1E1E;
    text-align:center;
}}
.container {{
    max-width:1100px;
    margin:0 auto;
    padding:0 20px 40px 20px;
}}
h1 {{
    margin:40px 0 30px 0;
    font-size:36px;
    color:#ffffff;
}}
.top-cards {{
    display:flex;
    justify-content:center;
    gap:40px;
    margin:30px 0;
    flex-wrap:wrap;
}}
.card {{
    background:#363636;
    width:260px;
    padding:25px;
    border-radius:18px;
    box-shadow:0 0 12px rgba(0,150,255,0.6);
}}
.card h3 {{
    font-size:20px;
    color:#ffffff;
}}
.card h2 {{
    font-size:36px;
    color:#0096ff;
    margin-top:15px;
}}
.available {{
    font-size:28px;
    margin:20px 0;
    font-weight:bold;
    color:#ffffff;
}}
.slots {{
    display:flex;
    justify-content:center;
    gap:40px;
    margin:30px 0;
    flex-wrap:wrap;
}}
.slot {{
    width:160px;
    height:180px;
    border-radius:20px;
    color:white;
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
}}
.full {{
    background:#ec0000;
    box-shadow:0 0 15px rgba(255,0,0,0.6);
}}
.open {{
    background:#118100;
    box-shadow:0 0 15px rgba(0,255,0,0.6);
}}
.control {{
    background:#363636;
    width:100%;
    margin:40px 0;
    padding:40px;
    border-radius:20px;
    box-shadow:0 0 12px rgba(0,150,255,0.6);
}}
.control h2 {{
    font-size:28px;
    margin-bottom:30px;
    color:#ffffff;
}}
.btn {{
    padding:15px 50px;
    font-size:18px;
    border:none;
    border-radius:30px;
    margin:15px;
    color:#ffffff;
    cursor:pointer;
}}
.btn-open {{
    background:#ec0000;
}}
.btn-close {{
    background:#118100;
}}
</style>
</head>

<body>
<div class="container">

<h1>Smart Parking Management Dashboard</h1>

<div class="top-cards">
    <div class="card">
        <h3>Temperature Status</h3>
        <h2>{temp}°C</h2>
    </div>

    <div class="card">
        <h3>Gate Status</h3>
        <h2>{gate_status}</h2>
    </div>

    <div class="card">
        <h3>Relay Status</h3>
        <h2>{relay_status}</h2>
    </div>
</div>

<div class="available">
Available Parking Slot : {available}
</div>

<div class="slots">
    <div class="{slot_class(slot1)}"><h3>Slot 1</h3><h2>{slot1}</h2></div>
    <div class="{slot_class(slot2)}"><h3>Slot 2</h3><h2>{slot2}</h2></div>
    <div class="{slot_class(slot3)}"><h3>Slot 3</h3><h2>{slot3}</h2></div>
    <div class="{slot_class(slot4)}"><h3>Slot 4</h3><h2>{slot4}</h2></div>
    <div class="{slot_class(slot5)}"><h3>Slot 5</h3><h2>{slot5}</h2></div>
</div>

<div class="control">
<h2>Manual Gate Control</h2>
<a href="/open"><button class="btn btn-open">Open</button></a>
<a href="/close"><button class="btn btn-close">Close</button></a>
</div>

</div>
</body>
</html>"""
# =========================
# WEB SERVER
# =========================
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
server = socket.socket()
server.bind(addr)
server.listen(5)

print("Web server running...")

while True:
    conn, addr = server.accept()
    request = conn.recv(1024).decode()

    # Read temperature
    try:
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
    except:
        temperature = 0

    # Handle button press
    if '/open' in request:
        open_gate()
    if '/close' in request:
        close_gate()

    response = webpage(temperature)

    conn.send("HTTP/1.1 200 OK\n")
    conn.send("Content-Type: text/html\n")
    conn.send("Connection: close\n\n")
    conn.sendall(response)
    conn.close()
