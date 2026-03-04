from time import sleep_us
from lcd_api import (
    LcdApi,
    LCD_FUNCTION,
    LCD_FUNCTION_2L,
    LCD_ON_CTRL,
    LCD_ON_DISPLAY,
    LCD_ENTRY_MODE,
    LCD_ENTRY_INC,
)


MASK_RS = 0x01
MASK_E = 0x04
MASK_BL = 0x08


class I2cLcd(LcdApi):
    def __init__(self, i2c, i2c_addr, num_lines, num_columns, backlight=True):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.backlight = MASK_BL if backlight else 0
        self._byte(0)

        self._write_init_nibble(0x30)
        self._write_init_nibble(0x30)
        self._write_init_nibble(0x30)
        self._write_init_nibble(0x20)

        func = LCD_FUNCTION | (LCD_FUNCTION_2L if num_lines > 1 else 0)
        self.hal_write_command(func)
        self.hal_write_command(LCD_ON_CTRL | LCD_ON_DISPLAY)
        self.hal_write_command(LCD_ENTRY_MODE | LCD_ENTRY_INC)
        self.clear()

        super().__init__(num_lines, num_columns)

    def hal_write_command(self, cmd):
        self._write4(cmd, rs=False)

    def hal_write_data(self, data):
        self._write4(data, rs=True)

    def _write_init_nibble(self, nibble):
        self._nibble(nibble)
        self._strobe()

    def _write4(self, value, rs):
        high = value & 0xF0
        low = (value << 4) & 0xF0

        self._nibble(high, rs)
        self._strobe()
        self._nibble(low, rs)
        self._strobe()

    def _nibble(self, nib, rs=False):
        data = (nib & 0xF0) | (MASK_RS if rs else 0) | self.backlight
        self._byte(data)

    def _strobe(self):
        self._byte(self._last | MASK_E)
        sleep_us(1)
        self._byte(self._last & ~MASK_E)
        sleep_us(50)

    def _byte(self, value):
        self._last = value
        self.i2c.writeto(self.i2c_addr, bytes([value]))