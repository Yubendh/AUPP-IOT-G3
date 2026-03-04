from time import sleep_ms


LCD_CLR = 0x01
LCD_HOME = 0x02
LCD_ENTRY_MODE = 0x04
LCD_ENTRY_INC = 0x02
LCD_ON_CTRL = 0x08
LCD_ON_DISPLAY = 0x04
LCD_ON_CURSOR = 0x02
LCD_ON_BLINK = 0x01
LCD_FUNCTION = 0x20
LCD_FUNCTION_2L = 0x08
LCD_SET_DDRAM = 0x80


class LcdApi:
    def __init__(self, num_lines, num_columns):
        self.num_lines = num_lines
        self.num_columns = num_columns
        self.cursor_x = 0
        self.cursor_y = 0

    def clear(self):
        self.hal_write_command(LCD_CLR)
        sleep_ms(2)
        self.move_to(0, 0)

    def move_to(self, col, row):
        self.cursor_x = col
        self.cursor_y = row
        addr = col & 0x3F
        if row == 1:
            addr |= 0x40
        elif row == 2:
            addr |= 0x14
        elif row == 3:
            addr |= 0x54
        self.hal_write_command(LCD_SET_DDRAM | addr)

    def putchar(self, char):
        if char == "\n":
            self.cursor_y = (self.cursor_y + 1) % self.num_lines
            self.move_to(0, self.cursor_y)
            return

        self.hal_write_data(ord(char))
        self.cursor_x += 1
        if self.cursor_x >= self.num_columns:
            self.cursor_x = 0
            self.cursor_y = (self.cursor_y + 1) % self.num_lines
            self.move_to(self.cursor_x, self.cursor_y)

    def putstr(self, string):
        for char in string:
            self.putchar(char)

    def hal_write_command(self, cmd):
        raise NotImplementedError

    def hal_write_data(self, data):
        raise NotImplementedError