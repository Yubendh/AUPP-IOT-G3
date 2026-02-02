from machine import Pin, SoftI2C, time_pulse_us
from machine_i2c_lcd import I2cLcd
import network
import socket
import time
import dht
LED = Pin(2, Pin.OUT)
LED.off()
led_state = False

TRIG = Pin(27, Pin.OUT)
ECHO = Pin(26, Pin.IN)

DHT_PIN = 4
dht_sensor = dht.DHT11(Pin(DHT_PIN))

I2C_ADDR = 0x27
i2c = SoftI2C(sda=Pin(21), scl=Pin(22), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)
lcd.clear()
ssid = "Robotic WIFI"
password = "rbtWIFI@2025"

wifi = network.WLAN(network.STA_IF)
wifi.active(True)

ip_printed = False

def reset_wifi():
	try:
		wifi.active(False)
		time.sleep(1)
		wifi.active(True)
	except Exception:
		pass

def ensure_wifi():
	global ip_printed
	try:
		if wifi.isconnected():
			if not ip_printed:
				print("ESP32 IP address:", wifi.ifconfig()[0])
				ip_printed = True
			return True
	except OSError:
		print("WiFi state error, resetting...")
		reset_wifi()

	print("Connecting to WiFi...")
	try:
		wifi.connect(ssid, password)
	except OSError:
		print("WiFi connect error, resetting...")
		reset_wifi()
		try:
			wifi.connect(ssid, password)
		except OSError:
			print("WiFi connect failed")
			return False

	for _ in range(15):
		try:
			if wifi.isconnected():
				print("Connected!")
				print("ESP32 IP address:", wifi.ifconfig()[0])
				ip_printed = True
				return True
		except OSError:
			print("WiFi state error, resetting...")
			reset_wifi()
		time.sleep(1)
	print("WiFi not connected")
	return False

ensure_wifi()
def get_distance_cm():
	TRIG.value(0)
	time.sleep_us(2)

	TRIG.value(1)
	time.sleep_us(10)
	TRIG.value(0)

	duration = time_pulse_us(ECHO, 1, 30000)
	if duration < 0:
		return None

	distance = (duration * 0.0343) / 2
	return distance

def read_temperature_humidity():
	try:
		dht_sensor.measure()
		return dht_sensor.temperature(), dht_sensor.humidity()
	except Exception:
		return None, None

def lcd_write_line(line, text):
	if text is None:
		text = ""
	text = text[:16]
	lcd.move_to(0, line)
	if len(text) < 16:
		text = text + (" " * (16 - len(text)))
	lcd.putstr(text)

def scroll_text(line, text, delay=0.3):
	if text is None:
		text = ""

	if len(text) <= 16:
		lcd_write_line(line, text)
		return

	scroll = text + "   "
	for i in range(len(scroll)):
		part = scroll[i:i + 16]
		if len(part) < 16:
			part = part + (" " * (16 - len(part)))
		lcd_write_line(line, part)
		time.sleep(delay)

def lcd_clear_all():
	lcd_write_line(0, "")
	lcd_write_line(1, "")

addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
try:
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
except Exception:
	pass
try:
	s.bind(addr)
except OSError:
	try:
		s.close()
	except Exception:
		pass
		s = socket.socket()
		try:
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		except Exception:
			pass
		s.bind(addr)
s.listen(1)

print("Web server running...")
def url_decode(value):
	value = value.replace("+", " ")
	result = ""
	i = 0
	while i < len(value):
		if value[i] == "%" and i + 2 < len(value):
			try:
				result += chr(int(value[i + 1:i + 3], 16))
				i += 3
				continue
			except Exception:
				pass
		result += value[i]
		i += 1
	return result

def parse_path(request):
	if not request:
		return "/", ""
	line = request.split("\r\n")[0]
	parts = line.split(" ")
	if len(parts) < 2:
		return "/", ""
	path = parts[1]
	if "?" in path:
		return path.split("?", 1)
	return path, ""

def get_query_param(qs, name):
	for part in qs.split("&"):
		if "=" in part:
			key, value = part.split("=", 1)
			if key == name:
				return url_decode(value)
	return ""

def web_page(state, temp, hum, dist, last_text):
	if state:
		color = "green"
		status = "LED is ON"
	else:
		color = "red"
		status = "LED is OFF"

	temp_str = "--" if temp is None else "{:.1f} C".format(temp)
	hum_str = "--" if hum is None else "{:.0f} %".format(hum)
	dist_str = "--" if dist is None else "{:.1f} cm".format(dist)
	last_text_str = "" if last_text is None else last_text

	html = f"""
	<html>
	<head>
		<title>ESP32 Control</title>
		<meta http-equiv="refresh" content="2">
		<style>
			body {{ font-family: Arial; text-align: center; }}
			.circle {{ width: 80px; height: 80px; background-color: {color}; border-radius: 50%; margin: 20px auto; }}
			button {{ width: 180px; height: 45px; font-size: 16px; margin: 6px; }}
			input {{ width: 200px; height: 35px; font-size: 16px; }}
		</style>
	</head>
	<body>
		<h1>ESP32 LED + Sensors</h1>
		<div class="circle"></div>
		<h2>{status}</h2>

		<p><a href="/on"><button>LED ON</button></a></p>
		<p><a href="/off"><button>LED OFF</button></a></p>

		<h3>Sensor Values</h3>
		<p>Temperature: {temp_str}</p>
		<p>Humidity: {hum_str}</p>
		<p>Distance: {dist_str}</p>

		<h3>LCD Actions</h3>
		<p><a href="/show_distance"><button>Show Distance</button></a></p>
		<p><a href="/show_temp"><button>Show Temp</button></a></p>

		<h3>Send Text to LCD</h3>
		<form action="/send" method="get">
			<input type="text" name="text" placeholder="Enter text" value="{last_text_str}">
			<button type="submit">Send</button>
		</form>
	</body>
	</html>
	"""
	return html

last_temp = None
last_hum = None
last_dist = None
last_text = ""

while True:
	if not ensure_wifi():
		time.sleep(2)
		continue

	conn, addr = s.accept()
	request = conn.recv(1024).decode()
	path, qs = parse_path(request)

	temp, hum = read_temperature_humidity()
	dist = get_distance_cm()

	if temp is not None:
		last_temp = temp
	if hum is not None:
		last_hum = hum
	if dist is not None:
		last_dist = dist

	if path == "/on":
		LED.on()
		led_state = True
		print("LED ON")

	elif path == "/off":
		LED.off()
		led_state = False
		print("LED OFF")

	elif path == "/show_distance":
		if last_dist is None:
			lcd_write_line(0, "Out of range")
		else:
			lcd_write_line(0, "Dist: {:.1f}cm".format(last_dist))

	elif path == "/show_temp":
		if last_temp is None:
			lcd_write_line(1, "Temp error")
		else:
			lcd_write_line(1, "Temp: {:.1f}C".format(last_temp))

	elif path == "/send":
		text = get_query_param(qs, "text")
		if text:
			last_text = text
			lcd_clear_all()
			scroll_text(0, text)

	response = web_page(led_state, last_temp, last_hum, last_dist, last_text)
	conn.send("HTTP/1.1 200 OK\n")
	conn.send("Content-Type: text/html\n")
	conn.send("Connection: close\n\n")
	conn.sendall(response)
	conn.close()

