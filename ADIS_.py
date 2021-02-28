import spidev 
import RPi.GPIO as GPIO
import time

# ADIS 16490 USER self.regISTER MEMORY MAP

_PAGE_ID = 0x00 # Same for all pages

# PAGE 0x00

_DATA_CNT = 0x04
_SYS_E_FLAG = 0x08
_DIAG_STS = 0x0A
_TEMP_OUT = 0x0E
_X_GYRO_LOW = 0x10
_X_GYRO_OUT = 0x12
_Y_GYRO_LOW = 0x14
_Y_GYRO_OUT = 0x16
_Z_GYRO_LOW = 0x18
_Z_GYRO_OUT = 0x1A
_X_ACCL_LOW = 0x1C
_X_ACCL_OUT = 0x1E
_Y_ACCL_LOW = 0x20
_Y_ACCL_OUT = 0x22
_Z_ACCL_LOW = 0x24
_Z_ACCL_OUT = 0x26
_TIME_STAMP = 0x28
_X_DELTANG_LOW = 0x40
_X_DELTANG_OUT = 0x42
_Y_DELTANG_LOW = 0x44
_Y_DELTANG_OUT = 0x46
_Z_DELTANG_LOW = 0x48
_Z_DELTANG_OUT = 0x4A
_X_DELTVEL_LOW = 0x4C
_X_DELTVEL_OUT = 0x4E
_Y_DELTVEL_LOW = 0x50
_Y_DELTVEL_OUT = 0x52
_Z_DELTVEL_LOW = 0x54
_Z_DELTVEL_OUT = 0x56
_PROD_ID = 0x7E  

# PAGE 0x01 Reserved
# PAGE 0x02

_X_GYRO_SCALE = 0x04
_Y_GYRO_SCALE = 0x06
_Z_GYRO_SCALE = 0x08
_X_ACCL_SCALE = 0x0A
_Y_ACCL_SCALE = 0x0C
_Z_ACCL_SCALE = 0x0E
_XG_BIAS_LOW = 0x10
_XG_BIAS_HIGH = 0x12
_YG_BIAS_LOW = 0x14
_YG_BIAS_HIGH = 0x16
_ZG_BIAS_LOW = 0x18
_ZG_BIAS_HIGH = 0x1A
_XA_BIAS_LOW = 0x1C
_XA_BIAS_HIGH = 0x1E
_YA_BIAS_LOW = 0x20
_YA_BIAS_HIGH = 0x22
_ZA_BIAS_LOW = 0x24
_ZA_BIAS_HIGH = 0x26
_USER_SCR_1 = 0x74
_USER_SCR_2 = 0x76
_USER_SCR_3 = 0x78
_USER_SCR_4 = 0x7A
_FLSHCNT_LOW = 0x7C
_FLSHCNT_HIGH = 0x7E

# PAGE 0x03

_GLOB_CMD = 0x02
_FNCTIO_CTRL = 0x06
_GPIO_CTRL = 0x08
_CONFIG = 0x0A
_DEC_RATE = 0x0C
_NULL_CNFG = 0x0E
_SYNC_SCALE = 0x10
_FILTR_BANK_0 = 0x16
_FILTR_BANK_1 = 0x18
_FIRM_REV = 0x78
_FIRM_DM = 0x7A
_FIRM_Y = 0x7C
_BOOT_REV = 0x7E

# PAGE 0x04

_CAL_SIGTR_LWR = 0x04
_CAL_SIGTR_UPR = 0x06
_CAL_DRVTN_LWR = 0x08
_CAL_DRVTN_UPR = 0x0A
_CODE_SIGTR_LWR = 0x0C
_CODE_SIGTR_UPR = 0x0E
_CODE_DRVTN_LWR = 0x10
_CODE_DRVTN_UPR = 0x12
_SERIAL_NUM = 0x20


IRQ = 6  # GPIO connect to data redy
spi = spidev.SpiDev()  # Создаем объект SPI
spi.open(0, 0)  # Выбор номера порта и номера устройства(CS) шины SPI
spi.max_speed_hz = 15000000  # Задаём максимальную скорость работы шины SPI
spi.mode = 3  # Выбор режима работы SPI (от 0 до 3)
GPIO.setmode(GPIO.BCM)  # Выбор режима нумерации выводов GPIO
GPIO.setup(IRQ, GPIO.IN)  # Инициализация GPIO6 на ввод


def _spi_read(spi, reg):  # Функция считывания данных по SPI
    send = [0]*2  # Создаём список из двух элементов
    # В 0 ячейку списка записываем адрес, который указываем в параметре reg
    send[0] = reg 
    spi.writebytes(send)  # Отправляем байты по шине SPI
    # Считываем 2 байта по шине SPI. В итоге получаем список из двух значений [X, Y]
    resp = spi.readbytes(2)
    # Сдвигаем 8 бит ячейки 0 влево, затем используем лог.сложение с ячейкой 1
    resp = ((resp[0] << 8) | resp[1])
    return resp

def _spi_write(spi, reg, value):  # Функция записи данных по SPI
    send = [0]*2  # Создаём список из двух элементов
    # В 0 ячейку списка записываем адрес, который указываем в параметре reg и с помощью лог.ИЛИ указываем старший бит на запись
    send[0] = 0x80 | reg
    send[1] = value  # В 1 ячейку отправляем данные которые нужно записать
    spi.writebytes(send)  # Отправляем байты по шине SPI


class ADIS_16490:
    def __init__(self): 
        """Check the ADIS was found, read the coefficients and enable the sensor"""
        # Check device ID.
        GPIO.wait_for_edge(IRQ, GPIO.FALLING) # Ждём уровень спадающенго фронта (по докуметации)
        _spi_write(spi, _PAGE_ID, 0x00)  # Переключаемся на 1 стр
        GPIO.wait_for_edge(IRQ, GPIO.FALLING)  
        ADIS_PROD_ID = _spi_read(spi, _PROD_ID)
        if  ADIS_PROD_ID != 16490:  
            raise RuntimeError(f"Failed to find ADIS 16490! Chip ID {ADIS_PROD_ID}")        

    def _get(self, reg):
        GPIO.wait_for_edge(IRQ, GPIO.FALLING) 
        self.value = _spi_read(spi, reg)  # Считываем значение
        return self.value
   
    def _set(self, reg, value):
        GPIO.wait_for_edge(IRQ, GPIO.FALLING) 
        _spi_write(spi, reg, value) # Записываем данные в регистр

    def _select_page(self, page):
        GPIO.wait_for_edge(IRQ, GPIO.FALLING) 
        _spi_write(spi, _PAGE_ID, page)  # Переключаемся на страницу  

    def _unity(self, high, low):  # Функция объединения 16 битных чисел в 32 бита
        bit32 = ((high << 16) | (low & 0xFFFF))
        return bit32

    def _check(self, val, bits):  # Функция проверки значения на знак
        if((val & (1 << (bits-1))) != 0):  # Если отрицательное, то переводим в дополнительный код
            val = val - (1 << bits)
        return val   

    def temp(self):  # Функция чтения температуры
        self._select_page(0x00)
        self.temp = self._get(_TEMP_OUT)
        self.temp = self._check(self.temp, 16)  # Проверим число на знак
        return 0.01429 * self.temp + 25  # Применяем формулу расчёта температуры из datasheet


    def z_gyro(self):
        self._select_page(0x00)
        z_gyro_low = self._get(_Z_GYRO_LOW)
        z_gyro_out = self._get(_Z_GYRO_OUT)
        z_gyro_32 = self._unity(z_gyro_out, z_gyro_low)
        self.z_gyro_32 = self._check(z_gyro_32, 32)  # Проверим число на знак
        return self.z_gyro_32 * 0.005/65536
    
    def z_accl(self): 
        self._select_page(0x00)
        z_accl_low = self._get(_Z_ACCL_LOW)
        z_accl_out = self._get(_Z_ACCL_OUT)
        z_accl_32 = self._unity(z_accl_out, z_accl_low)
        self.z_accl_32 = self._check(z_accl_32, 32)  # Проверим число на знак
        return self.z_accl_32 * 0.5/65536

    # Количество значений в 1 секунду = 4250 / (dec_rate + 1)
    def read_decrate(self):
        self._select_page(0x03)
        self.decrate = self._get(_DEC_RATE)
        return self.decrate  

    def set_decrate(self, value):
        #Необходимо полученное число разделить на 2 части по 8 бит каждое
        decrate_low = value & 0xff
        decrate_high = (value >> 8) & 0xff
        self._select_page(0x03)
        self._set(_DEC_RATE, decrate_low)
        self._set(_DEC_RATE+1, decrate_high)


x = ADIS_16490()
y = ADIS_16490()
x.set_decrate(0)
temp = x.temp()
z_gyro = x.z_gyro()
z_accl = x.z_accl()
decrate = x.read_decrate()
print(temp)
print(z_gyro)
print(z_accl)
print(decrate)

























