import time

from config import TEST_SAMPLE_COUNT, TEST_SAMPLE_DELAY_MS
from main import get_system_output, handle_command


REQUIRED_OUTPUT_KEYS = (
    "slot_1",
    "slot_2",
    "slot_3",
    "available_slots",
    "system_status",
    "last_update",
)


def run(samples=TEST_SAMPLE_COUNT, delay_ms=TEST_SAMPLE_DELAY_MS):
    print("=== ESP32 SMOKE TEST START ===")
    passed = True

    for index in range(samples):
        output = get_system_output()
        missing = [key for key in REQUIRED_OUTPUT_KEYS if key not in output]
        if missing:
            passed = False
            print("FAIL output keys missing:", missing)
        else:
            print(
                "sample",
                index + 1,
                "slots:",
                output["slot_1"],
                output["slot_2"],
                output["slot_3"],
                "available:",
                output["available_slots"],
            )
        time.sleep_ms(delay_ms)

    status = handle_command("get_status", source="esp32_test")
    if not status.get("ok"):
        passed = False
        print("FAIL get_status command")

    refresh = handle_command("refresh_now", source="esp32_test")
    if not refresh.get("ok"):
        passed = False
        print("FAIL refresh_now command")

    unsupported = handle_command("invalid_command", source="esp32_test")
    if unsupported.get("ok") or unsupported.get("error") != "unsupported_command":
        passed = False
        print("FAIL unsupported command handling")

    if passed:
        print("=== ESP32 SMOKE TEST PASS ===")
    else:
        print("=== ESP32 SMOKE TEST FAIL ===")

    return passed
