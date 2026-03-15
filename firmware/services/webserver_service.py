# Web server service: dashboard + HTTP command routing through main controller.

import network
import socket
import time
import __main__
try:
    import ujson as json
except ImportError:
    import json

from config import (
    WEBSERVER_BACKLOG,
    WEBSERVER_HOST,
    WEBSERVER_PORT,
    WIFI_CONNECT_RETRIES,
    WIFI_PASSWORD,
    WIFI_SSID,
)
try:
    handle_command = __main__.handle_command
except AttributeError:
    from main import handle_command


wifi = network.WLAN(network.STA_IF)
wifi.active(True)


def ensure_wifi():
    if wifi.isconnected():
        return True

    if not wifi.active():
        try:
            wifi.active(True)
            time.sleep_ms(100)
        except Exception as exc:
            print("Web Wi-Fi activate error:", exc)
            return False

    try:
        wifi.connect(WIFI_SSID, WIFI_PASSWORD)
    except Exception as exc:
        print("Web Wi-Fi connect error:", exc)
        return False

    for _ in range(WIFI_CONNECT_RETRIES):
        if wifi.isconnected():
            return True
        time.sleep(1)
    return False


def get_web_url():
    return "http://{}:{}/".format(wifi.ifconfig()[0], WEBSERVER_PORT)


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


PAGE_STYLE = (
    "body{margin:0;font-family:Arial;background:#1e1e1e;color:#fff;text-align:center}"
    ".c{padding:16px}.top,.slots{display:flex;flex-wrap:wrap;justify-content:center;gap:12px}"
    ".card,.ctl,.slot{background:#363636;border-radius:14px;padding:14px}"
    ".card{min-width:120px}.slot{width:110px}.full{background:#a00}.open{background:#070}"
    ".btn{display:inline-block;margin:8px;padding:12px 26px;border-radius:22px;color:#fff;text-decoration:none}"
    ".o{background:#a00}.x{background:#070}"
)


PAGE_TEMPLATE = """<!doctype html><html><head><title>Parking</title><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="5"><style>{style}</style></head><body><div class="c"><h2>Parking</h2><div class="top"><div class="card">Temp<br>{temp}C</div><div class="card">Hum<br>{humidity}%</div><div class="card">Gate<br>{gate_status}</div></div><p>Slots: {available}</p><div class="slots">{slot_cards}</div><div class="ctl"><a class="btn o" href="/open">Open</a><a class="btn x" href="/close">Close</a></div></div></body></html>"""


def webpage(temp):
    dashboard = get_dashboard_state()
    slot_statuses = dashboard.get("slot_statuses", [])
    gate_status = dashboard.get("gate_status", "-")
    humidity = dashboard.get("humidity_pct", "-")
    available = dashboard.get("available_slots")

    if available is None:
        available = 0
        for status in slot_statuses:
            if status == "OPEN":
                available += 1

    slot_cards = []
    for index, status in enumerate(slot_statuses):
        slot_cards.append(
            '<div class="{slot_class}">S{slot_number}<br>{status}</div>'.format(
                slot_class=slot_class(status),
                slot_number=index + 1,
                status=status,
            )
        )

    return PAGE_TEMPLATE.format(
        style=PAGE_STYLE,
        temp=temp,
        humidity=humidity,
        gate_status=gate_status,
        available=available,
        slot_cards="".join(slot_cards),
    )


def get_request_path(request_text):
    first_line = request_text.split("\r\n", 1)[0]
    parts = first_line.split(" ")
    if len(parts) >= 2:
        return parts[1]
    return "/"


def json_response(payload):
    return json.dumps(payload), "application/json"


def handle_api_request(path):
    if path == "/api/status":
        return json_response(handle_command("get_status", source="web_api"))

    if path == "/api/open":
        return json_response(handle_command("open_gate", source="web_api"))

    if path == "/api/close":
        return json_response(handle_command("close_gate", source="web_api"))

    if path == "/api/slots":
        return json_response(handle_command("get_slots", source="web_api"))

    if path == "/api/temp":
        return json_response(handle_command("get_temp", source="web_api"))

    return json_response(
        {
            "ok": False,
            "error": "not_found",
            "path": path,
        }
    )


def handle_request(request_text):
    path = get_request_path(request_text)

    if path.startswith("/api/"):
        return handle_api_request(path)

    if path == "/open":
        handle_command("open_gate", source="web")
    elif path == "/close":
        handle_command("close_gate", source="web")
    elif path == "/light_on":
        handle_command("light_on", source="web")
    elif path == "/light_off":
        handle_command("light_off", source="web")

    return webpage(get_temperature()), "text/html"


def run_webserver_loop():
    if not ensure_wifi():
        print("Web server Wi-Fi connection failed.")
        return

    addr = socket.getaddrinfo(WEBSERVER_HOST, WEBSERVER_PORT)[0][-1]
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(addr)
    server.listen(WEBSERVER_BACKLOG)

    print("Web server running at {}".format(get_web_url()))
    print("Website link: {}".format(get_web_url()))

    while True:
        conn = None
        try:
            conn, _ = server.accept()
            request = conn.recv(1024).decode()
            response, content_type = handle_request(request)
            conn.send("HTTP/1.1 200 OK\r\n")
            conn.send("Content-Type: {}\r\n".format(content_type))
            conn.send("Connection: close\r\n\r\n")
            conn.sendall(response)
        except Exception as exc:
            err = str(exc)
            if "ECONNABORTED" not in err and "ENOTCONN" not in err:
                print("Web server error:", exc)
        finally:
            if conn is not None:
                conn.close()


def run():
    run_webserver_loop()


if __name__ == "__main__":
    run()
