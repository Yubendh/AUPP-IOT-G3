# ICT 360 – Introduction to Internet of Things (IoT)

# Final Project: ESP32-CAM + Multi-Light Sensor ESP32

## Team Members
- Meouk Sovannarith  
- Vanthan Buth Yubendh  
- Lim Houykea  
- Deth Sokunboranich  

---

# Table of Contents
1. [Project Overview](#i-project-overview)  
2. [Problem and Proposed Solution](#ii-problem-and-proposed-solution)  
3. [Components](#iii-components)  
4. [Technical Approach](#iv-technical-approach)  
5. [Result Demonstration](#v-result-demonstration)  
6. [Challenges and Future Improvements](#vi-challenges-and-future-improvements)  

---

# I. Project Overview

This project presents a **Hand Gesture Recognition & Multiple Sensors Control System** using ESP32 and ESP32-CAM technology. The system is designed to recognize hand gestures and convert them into real-time actions such as controlling smart lighting and displaying text.

The project combines IoT technology, gesture recognition, sensor integration, and wireless communication to create a more interactive and accessible smart system.

### Main Objectives
- Improve accessibility through gesture-based control
- Enable smart lighting automation
- Demonstrate real-time IoT communication
- Integrate multiple sensors into one system

### Key Features
- Hand gesture recognition using ESP32-CAM
- Smart lighting control with servo motor
- Distance validation using ultrasonic sensor
- RGB LED color feedback using NeoPixel
- Real-time communication between ESP32 boards

---

# II. Problem and Proposed Solution

## Problem

According to research, many disabled individuals experience barriers in daily communication and interaction. Traditional systems often rely on physical switches or manual control, which may not be convenient for everyone.

Challenges include:
- Difficulty in communication
- Limited accessibility
- Dependence on manual switches
- Lack of smart interaction systems

## Proposed Solution

To address these issues, our team developed a smart IoT-based system that recognizes hand gestures and converts them into actions.

The system can:
- Detect hand gestures using ESP32-CAM
- Convert gestures into real-time commands
- Control lighting automatically
- Provide visual feedback using RGB LEDs
- Improve accessibility and independent living

The solution combines computer vision, embedded systems, and sensor technologies into one integrated platform.

---

# III. Components

The following hardware components were used in this project:

| Component | Purpose |
|---|---|
| ESP32-CAM | Hand gesture detection and image processing |
| ESP32 Development Board | Main controller and communication |
| Ultrasonic Sensor (HC-SR04) | Distance validation |
| Servo Motor | Physically toggle light switch |
| NeoPixel RGB LED | Visual feedback and color indication |
| LCD Display (I2C) | Display system information and messages |
| Jumper Wires & Breadboard | Circuit connections |

---

# IV. Technical Approach

The system uses two ESP32-based modules working together through wireless communication.

- The ESP32-CAM captures hand gestures.
- The gesture is processed and assigned to a specific command.
- The ultrasonic sensor validates whether the object is within range to avoid false detection.
- The ESP32 board controls the servo motor and RGB LEDs based on the recognized gesture.
- LCD display shows system status and feedback.

## System Flowchart

![System Flowchart](./Screenshot%202026-05-08%20at%2010.14.02.png)

## Flow Description

1. User performs hand gesture  
2. ESP32-CAM captures image  
3. Gesture recognition process starts  
4. Ultrasonic sensor validates distance  
5. Command sent to ESP32  
6. Servo motor controls light switch  
7. NeoPixel LEDs display visual feedback  
8. LCD updates system information  

### Technologies Used
- ESP32 / ESP32-CAM
- Arduino IDE
- Embedded C/C++
- IoT Wireless Communication
- Sensor Integration

---

# V. Result Demonstration

The project was successfully implemented and tested.

### Demonstrated Functions
- Accurate hand gesture detection
- Real-time smart lighting control
- Servo motor successfully toggled switches
- RGB LED changed color according to gestures
- Distance validation reduced false positives
- Smooth communication between ESP32 boards

The system demonstrated effective IoT automation and accessibility-focused interaction.

---

# VI. Challenges and Future Improvements

## Challenges

During development, several technical challenges were encountered:

### Gesture Recognition Accuracy
- Different lighting conditions affected camera detection
- Hand position variations reduced accuracy

### Real-Time Synchronization
- Maintaining smooth communication between ESP32 devices
- Avoiding command conflicts and delays

---

## Future Improvements

Several features can be added in the future to improve the system:

### Expanded Gesture Library
- Add more gesture commands
- Support additional smart device controls

### Website Integration
- Enable remote monitoring and control
- Display real-time system status online

### Additional Improvements
- AI-based gesture recognition
- Mobile application support
- Cloud data storage
- Smart home integration
