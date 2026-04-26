from pathlib import Path

BASE_DIR      = Path(__file__).parent.parent
RESOURCES_DIR = BASE_DIR / "resources"
MODEL_DIR     = RESOURCES_DIR / "model"

# Update this IP after the ESP32-CAM connects to WiFi and reports its address
STREAM_URL = "http://192.168.1.213:81/stream"

MODEL_PATH     = MODEL_DIR / "gesture_mlp.keras"
CLASSES_PATH   = MODEL_DIR / "classes.pkl"
LANDMARKER_PATH = MODEL_DIR / "hand_landmarker.task"

CONFIDENCE_THRESHOLD = 0.85
DEBOUNCE_FRAMES      = 3
