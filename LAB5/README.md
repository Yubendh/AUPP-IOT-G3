# LAB 5: Smart Color Detection & Control with MIT App
# Team memebers: 
- Lim Houykea
- Deth Sokunboranich
- Meouk Sovannarith
- Vanthan Buth Yubendh

## Task 1 and 2 - RGB Reading & Color Classification 

![task1](images&videos/Screenshot%202026-04-06%20at%2001.03.34.png)

- The ESP32 reads RGB Values (Red, Green, Blue, Clear) from the TCS34725 sensor using I2C
- RGB values are displayed on the Serial Monitor in real time
- There is a rule-based algorithm that is used to classify colors based on RGB comparison:
  - R > G and R > B → RED
  - G > R and G > B → GREEN
  - B > R and B > G → BLUE
  - Otherwise → UNKNOWN
- The system outputs RGB values and detected color (RED, GREEN, and BLUE)

## Task 3 - NeoPixel Control

https://youtu.be/AIlWcFbYXRU

- NeoPixel LED is controlled based on detected color from the system
- ESP32 sends RGB values to the NeoPixel
- LED color changes according to:
  - RED -> LED show red
  - GREEN -> LED show green
  - BLUE -> LED show blue
 - It also provides real-time visual feedback of detected color and confirms correct integration between color detection and LED output

## Task 4 - Motor Control (PWM)

https://youtu.be/hhPX861pLvA

- DC moto is controlled using PWM
- Motor speed is adjusted based on detected color:
  - RED -> High speed (PWM = 700)
  - GREEN -> Medium speed (PWM = 500)
  - BLUE -> Low speed (PWM = 300)
 - ESP32 sends PWM signals to motor driver to control speed
 - Motor direction (forward, stop, backward) and has automatic control of motor based on sensor input

## Task 5 - MIT App Integration 
## MIT App File
![app](images&videos/photo_2026-04-06%2001.50.15.jpeg)
![app](images&videos/Screenshot%202026-04-06%20at%2001.47.34.png)

- MIT App Inventor app is developed to control and monitor the system
- App communicates with ESP32 using HTTP requests over Wi-Fi
- The feature is to :
  - displays detected color in real time
  - buttons for motor control: Forward, Stop, Backward
  - AUTO and MANUAL modes for system control
  - RGB sliders to manually set NeoPixel color
  - Motor speed control using slider
  - App retrieves data from ESP32 (/status) and updates UI
  - User inputs are sent to ESP32 (/set_rgb, /set_speed)
  - Confirms integration between and hardware and software

## DEMO Video 

https://youtu.be/oJMJ_5Z71Dc

## System Flowchart
