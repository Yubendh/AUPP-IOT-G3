# Web server service: dashboard + HTTP command routing through main controller.

import network
import socket
import time

from config import (
    WEBSERVER_BACKLOG,
    WEBSERVER_HOST,
    WEBSERVER_PORT,
    WIFI_CONNECT_RETRIES,
    WIFI_PASSWORD,
    WIFI_SSID,
)
from main import handle_command


wifi = network.WLAN(network.STA_IF)
wifi.active(True)

def ensure_wifi():
    if wifi.isconnected():
        return True

    wifi.connect(WIFI_SSID, WIFI_PASSWORD)
    for _ in range(WIFI_CONNECT_RETRIES):
        if wifi.isconnected():
            return True
        time.sleep(1)
    return False


def get_temperature():
    status = get_dashboard_state()
    return status.get("temp_c", "N/A")


def get_dashboard_state():
    response = handle_command("get_status", source="web")
    if not response.get("ok"):
        return {}
    return response.get("data", {})


def slot_class(status):
    if status == "OPEN":
        return "slot open"
    return "slot full"


def webpage(temp):
    dashboard = get_dashboard_state()
    slot_statuses = dashboard.get("slot_statuses", [])
    gate_status = dashboard.get("gate_status", "UNKNOWN")
    relay_status = dashboard.get("relay_status", "DISABLED")
    humidity = dashboard.get("humidity_pct", "N/A")
    available = dashboard.get("available_slots")

    if available is None:
        available = 0
        for status in slot_statuses:
            if status == "OPEN":
                available += 1

    slot_cards = []
    for index, status in enumerate(slot_statuses):
        slot_cards.append(
            '<div class="{slot_class}"><h3>Slot {slot_number}</h3><h2>{status}</h2></div>'.format(
                slot_class=slot_class(status),
                slot_number=index + 1,
                status=status,
            )
        )

    return """<!DOCTYPE html>
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
        <h2>{temp} C</h2>
    </div>

    <div class="card">
        <h3>Humidity Status</h3>
        <h2>{humidity} %</h2>
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
    {slot_cards}
</div>

<div class="control">
<h2>Manual Gate Control</h2>
<a href="/open"><button class="btn btn-open">Open</button></a>
<a href="/close"><button class="btn btn-close">Close</button></a>
</div>

</div>
</body>
</html>""".format(
        temp=temp,
        humidity=humidity,
        gate_status=gate_status,
        relay_status=relay_status,
        available=available,
        slot_cards="".join(slot_cards),
    )


def handle_request(request_text):
    if "GET /open " in request_text:
        handle_command("open_gate", source="web")
    elif "GET /close " in request_text:
        handle_command("close_gate", source="web")
    elif "GET /light_on " in request_text:
        handle_command("light_on", source="web")
    elif "GET /light_off " in request_text:
        handle_command("light_off", source="web")

    return webpage(get_temperature())


def run_webserver_loop():
    if not ensure_wifi():
        print("Web server Wi-Fi connection failed.")
        return

    addr = socket.getaddrinfo(WEBSERVER_HOST, WEBSERVER_PORT)[0][-1]
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(addr)
    server.listen(WEBSERVER_BACKLOG)

    print("Web server running at http://{}:{}/".format(wifi.ifconfig()[0], WEBSERVER_PORT))

    while True:
        conn = None
        try:
            conn, _ = server.accept()
            request = conn.recv(1024).decode()
            response = handle_request(request)
            conn.send("HTTP/1.1 200 OK\r\n")
            conn.send("Content-Type: text/html\r\n")
            conn.send("Connection: close\r\n\r\n")
            conn.sendall(response)
        except Exception as exc:
            print("Web server error:", exc)
        finally:
            if conn is not None:
                conn.close()


def run():
    run_webserver_loop()


if __name__ == "__main__":
    run()
