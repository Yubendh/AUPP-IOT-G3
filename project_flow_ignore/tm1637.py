from machine import Pin
from time import sleep_us


_SEGMENTS = [
    0x3F,  # 0
    0x06,  # 1
    0x5B,  # 2
    0x4F,  # 3
    0x66,  # 4
    0x6D,  # 5
    0x7D,  # 6
    0x07,  # 7
    0x7F,  # 8
    0x6F,  # 9
]

LETTER_F = 0x71
LETTER_U = 0x3E
LETTER_L = 0x38


class TM1637:
    def __init__(self, clk_pin, dio_pin, brightness=4):
        self.clk = Pin(clk_pin, Pin.OUT, value=1)
        self.dio = Pin(dio_pin, Pin.OUT, value=1)
        self.brightness(brightness)

    def _start(self):
        self.dio.value(1)
        self.clk.value(1)
        sleep_us(2)
        self.dio.value(0)

    def _stop(self):
        self.clk.value(0)
        sleep_us(2)
        self.dio.value(0)
        sleep_us(2)
        self.clk.value(1)
        sleep_us(2)
        self.dio.value(1)

    def _write_byte(self, value):
        for _ in range(8):
            self.clk.value(0)
            self.dio.value(value & 0x01)
            value >>= 1
            sleep_us(3)
            self.clk.value(1)
            sleep_us(3)

        self.clk.value(0)
        self.dio.init(Pin.IN)
        sleep_us(5)
        self.clk.value(1)
        sleep_us(5)
        self.clk.value(0)
        self.dio.init(Pin.OUT, value=0)

    def brightness(self, value):
        if value < 0:
            value = 0
        elif value > 7:
            value = 7
        self._brightness = value
        self._cmd_display = 0x88 | value

    def write(self, segments):
        self._start()
        self._write_byte(0x40)
        self._stop()

        self._start()
        self._write_byte(0xC0)
        for seg in segments:
            self._write_byte(seg)
        self._stop()

        self._start()
        self._write_byte(self._cmd_display)
        self._stop()

    def show_number(self, number):
        if number < 0:
            number = 0
        if number > 9999:
            number = 9999

        text = "{:>4}".format(number)
        segments = []
        for ch in text:
            if ch == " ":
                segments.append(0x00)
            else:
                segments.append(_SEGMENTS[ord(ch) - 48])
        self.write(segments)

    def show_full(self):
        self.write([LETTER_F, LETTER_U, LETTER_L, LETTER_L])

    def clear(self):
        self.write([0x00, 0x00, 0x00, 0x00])