from machine import I2C


class DS3231:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr

    def bcd2dec(self, bcd):
        return (bcd >> 4) * 10 + (bcd & 0x0F)

    def dec2bcd(self, dec):
        return (dec // 10 << 4) + (dec % 10)

    def get_time(self):
        data = self.i2c.readfrom_mem(self.addr, 0x00, 7)
        second = self.bcd2dec(data[0])
        minute = self.bcd2dec(data[1])
        hour = self.bcd2dec(data[2])
        day = self.bcd2dec(data[4])
        month = self.bcd2dec(data[5])
        year = self.bcd2dec(data[6]) + 2000
        return (year, month, day, hour, minute, second)

    def set_time(self, year, month, day, hour, minute, second):
        year = year - 2000

        data = bytearray(7)
        data[0] = self.dec2bcd(second)
        data[1] = self.dec2bcd(minute)
        data[2] = self.dec2bcd(hour)
        data[3] = self.dec2bcd(1)
        data[4] = self.dec2bcd(day)
        data[5] = self.dec2bcd(month)
        data[6] = self.dec2bcd(year)

        self.i2c.writeto_mem(self.addr, 0x00, data)
