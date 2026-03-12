# LAB 4: Multi-Sensor IoT Monitoring with Grafana Dashboard
# Team Members : 
- Meouk Sovannarith
- Vanthan Buth Yubendh
- Lim Houykea
- Deth Sokunboranich

Explaning system logic
## Task 1 - Gas Filtering (Moving Average)
- The MQ-5 gas sensor reads an analog voltage -> converts it into a number between 0 and 4095
- Problem: There are noise because number isn't stable even when the gas level hasn't actually changed
- Resolution: user moving average
- Explaination: everytime ESP32 takes a reading, it stores that number into a list, which it holds the last 5 readings. Afterward, the code find the average of the readings and printed to the screen.
- Finally, it sends to Node-RED

## Task 2 - Gas risk clarification
- The system decide gas level is safe or not according to the moving average calculations
- The code checks if the average number below 2100, if yes it will display "SAFE"
- If the average number is below 2600, it displays "WARNING"
- If it's more than 2600 then it will display "DANGER"

## Task 3 - Fever Detection
- After the temperature is read, the code checks a single condition -> Is the temperature 32.5 degree celcius or higher?
- If yes, fever_flag is set to 1, which means fever is detected
- If the temperature is below that threshold, fever_flag is set to 0, meaning the temperature is normal.

## Task 4 - Pressure, Altitude, and Full Data Transmission
- The BMP280 sensor measures air pressure (hPa) and altitude (meters)
- Unlike the gas sensor, these values do not need any filtering; they are sent exactly as they are
- The DS3231 clock gives the exact date and time for every reading, so we know precisely when each data was recorded
- All results from Task 1, Task 2, Task 3, and Task 4 are combined into one single JSON message
- That message is sent over Wi-Fi to Node-RED every 5 seconds using HTTP POST
- Node-RED saves the data into InfluxDB, and Grafana reads it to display live graphs and status panels on the dashboard