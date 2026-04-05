import time

class TCS34725:

    COMMAND_BIT = 0x80
    ENABLE = 0x00
    ENABLE_AEN = 0x02
    ENABLE_PON = 0x01
    ATIME = 0x01
    CONTROL = 0x0F
    ID = 0x12
    CDATA = 0x14

    def __init__(self, i2c, address=0x29):
        self.i2c = i2c
        self.address = address

        self.write(self.ENABLE, self.ENABLE_PON)
        time.sleep_ms(10)
        self.write(self.ENABLE, self.ENABLE_PON | self.ENABLE_AEN)

    def write(self, reg, value):
        self.i2c.writeto_mem(self.address, reg | self.COMMAND_BIT, bytes([value]))

    def read(self, reg, nbytes):
        return self.i2c.readfrom_mem(self.address, reg | self.COMMAND_BIT, nbytes)

    def read16(self, reg):
        data = self.read(reg,2)
        return data[1]<<8 | data[0]

    def read_raw(self):
        c = self.read16(self.CDATA)
        r = self.read16(self.CDATA+2)
        g = self.read16(self.CDATA+4)
        b = self.read16(self.CDATA+6)
        return (r,g,b,c)
