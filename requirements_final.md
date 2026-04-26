Final Project: ESP32-CAM + Multi-
Sensor ESP32
1. Project Overview
In this final project, students will design and implement a smart vision-based system using
ESP32-CAM combined with a second ESP32 that connects to sensors and actuators.
The system must capture visual data, perform detection or recognition, communicate with
another ESP32, and trigger real-world actions based on combined logic.
2. Core System Architecture (Mandatory)
Camera System (ESP32-CAM-Detection / recognition / tracking / classification)
Communication (WiFi / HTTP / Serial)
Control System (ESP32 with sensors and actuators)
3. Mandatory Requirements
• Camera-based system (ESP32-CAM)
• Second ESP32 with at least TWO components:
- 2 sensors OR
- 2 actuators OR
- 1 sensor + 1 actuator
• Communication between systems
• Real-world action (motor, servo, relay, buzzer, etc.)
4. Decision Logic Requirement
Projects MUST combine camera detection and sensor input.
Example:
IF camera detects person AND PIR detects motion → buzzer ON
IF camera detects car AND ultrasonic < 15 cm → open gate
Simple single-condition systems are NOT accepted.
5. Deliverables
Students must submit ALL of the following:
1. Source Code
2. Report in Github
3. Video Project
4. Live In-Class Presentation
6. Video Explanation Requirements
The video must include:
• Project introduction (team + system name)
• Explanation of system architecture
• Explanation of logic and decision-making
• Demonstration of the system working
• Behind the scene
The video should clearly explain HOW the system works, not just show results.
7. In-Class Presentation Requirements
Each group must present LIVE in class.
Must include:
• Problem statement
• System architecture explanation
• Design decisions
• Live demo
• Q&A with instructor
All members must participate.
8. Evaluation Rubric
• Camera / Vision System – 20%
• Sensor & Actuator Integration – 20%
• Decision Logic – 10%
• Code Quality – 10%
• Video Explanation – 15%
• In-Class Presentation – 20%
• Creativity – 5%
9. Rules
• Must include camera + second ESP32
• Must include at least two sensors/actuators
• Must demonstrate communication
• No copying between groups
• Live demo required during presentation