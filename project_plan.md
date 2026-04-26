- Second ESP32 + DC Motor system: a second ESP32 board is connected to a DC motor, where the motor physically actuates a light switch toggle upon receiving a recognized gesture command from the ESP32-CAM over Wi-Fi. If permitted, the relay module acts as a safety switch, cutting or supplying power to the light circuit in response to the motor's position, completing the real-world action of turning a light on or off through gesture control.
-RGB LED Strip Visual Feedback: the LED strip changes color based on the recognized gesture, providing immediate visual confirmation of what gesture was detected, for example, thumbs up = green, open palm = blue. This doubles as an accessibility feature for people nearby who may also have hearing impairments.
-Ultrasonic Sensor Proximity Wake: the ultrasonic sensor on the second ESP32 detects when a user approaches within a set range, automatically activating the camera system from a low-power idle state. This feature adds edge logic: the camera only begins inferencing when a person is actually present, reducing unnecessary ESP32 chip processing. 
-Combined Decision Logic : the system only triggers the motor/light switch when a certain valid gestures are recognized and the ultrasonic sensor confirms a user is within range, preventing false triggers/accidents.



References
-Nagish. (2025, November 19). New Survey Reveals Ongoing Communication Barriers for Deaf and Hard-of-Hearing in Social, Medical, and Professional Settings. PR Newswire. https://www.prnewswire.com/news-releases/new-survey-reveals-ongoing-communication-barriers-for-deaf-and-hard-of-hearing-in-social-medical-and-professional-settings-302619991.html
-Theara, S. (2026). ICT 360: Internet of Things, Section 002 [Course]. Canvas Learning Management System. American University of Phnom Penh. 
Overview
Problem statement
Many people with disabilities across the globe often struggle to communicate with others due to their conditions, which rely on sign language and hearing issues. This creates significant barriers in daily interactions and at work. According to Nagish (2025), 62% of deaf participants and 6% of hard-of-hearing people find it challenging to communicate, which results in their loss of opportunity and career growth.
Project objective
As technology evolves, it’s a chance to utilize technology that effectively assists people. This project aims to implement hand gesture recognition to break the barrier in communication. By allowing people with disabilities to utilize their hand gestures, the system will generate text accordingly along with control of smart lighting. 

Components used
- Implement hand gesture recognition on the ESP32-CAM using TinyML/Edge Impulse.
-Integrate a second ESP32 with 1 sensor and 1 actuator (ultrasonic + big RGB LED strip).
-Use WiFi communication between the two boards.
-Trigger dynamic changes on a big color-changing LED light using mandatory combined decision logic.
-Create a visually impressive prototype suitable for a live demo and video.

Main Functionalities/Features
-ESP32-CAM: One ESP32 board is attached with a camera module to detect and capture hand gestures, storing the image data, which is then used to train and deploy a classification model via the Edge Impulse platform.
