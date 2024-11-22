from machine import Pin, SPI
from micropython import const
import time

class MI0283QT2_lvgl(object):
    """
    For orientation related information and more information about the display controller consult the HX8347-D datasheet
    For more information about the touch screen controller consult the XPT2046 / ADS7846 datasheet

    IMPORTANT! Keep in mind because SPI bus is shared, touch screen will not be detected while the screen is
    being drawn on.
    """
    
    #Command set registers
    POWER_CONTROL_INTERNAL_USE_1 = const(0xEA)
    POWER_CONTROL_INTERNAL_USE_2 = const(0xEB)
    SOURCE_CONTROL_INTERNAL_USE_1 = const(0xEC)
    SOURCE_CONTROL_INTERNAL_USE_2 = const(0xED)
    SOURCE_OP_CONTROL_NORMAL = const(0xE8)
    SOURCE_OP_CONTROL_IDLE = const(0xE9)
    DISPLAY_CONTROL_2 = const(0x27)
    POWER_CONTROL_2 = const(0x1B)
    POWER_CONTROL_1 = const(0x1A)
    VCOM_CONTROL_1 = const(0x23)
    VCOM_CONTROL_2 = const(0x24)
    VCOM_CONTROL_3 = const(0x25)
    OSC_CONTROL_2 = const(0x18)
    OSC_CONTROL_1 = const(0x19)
    DISPLAY_MODE_CONTROL = const(0x01)
    POWER_CONTROL_6 = const(0x1F)
    COLMOD = const(0x17)
    PANEL_CHARACTERISTIC = const(0x36)
    MEMORY_ACCESS_CONTROL = const(0x16)
    COLUMN_ADDRESS_START_1 = const(0x03)
    COLUMN_ADDRESS_START_2 = const(0x02)
    COLUMN_ADDRESS_END_1 = const(0x05)
    COLUMN_ADDRESS_END_2 = const(0x04)
    ROW_ADDRESS_START_1 = const(0x07)
    ROW_ADDRESS_START_2 = const(0x06)
    ROW_ADDRESS_END_1 = const(0x09)
    ROW_ADDRESS_END_2 = const(0x08)
    DISPLAY_CONTROL_3 = const(0x28)
    
    #LCD commands
    LCD_ID = const(0)
    LCD_DATA = const((0x72)|(LCD_ID<<2))
    LCD_REGISTER = const((0x70)|(LCD_ID<<2))
    
    #Touch commands
    ADS_CMD_START = const(0x80)
    ADS_CMD_12BIT = const(0x00)
    ADS_CMD_8BIT = const(0x08)
    ADS_CMD_DIFF = const(0x00)
    ADS_CMD_X_POS = const(0x50)
    ADS_CMD_Y_POS = const(0x10)
    ADS_CMD_Z1_POS = const(0x30)
    ADS_CMD_Z2_POS = const(0x40)
    ADS_CMD_ALWAYS_ON = const(0x02)
    ADS_CMD_POWER_OFF = const(0x00)

    #Minimal pressure for touch detection
    MIN_PRESSURE = const(2) #Value range from 1 to 254
    
    #Touch offset
    X_MIN = const(170)
    X_MAX = const(3815)
    Y_MIN = const(286)
    Y_MAX = const(3839)
    
    DISPLAY_SPI_SPEED = const(24000000) 
    TOUCH_SPI_SPEED = const(1000000)
    
    #Default screen size values
    LCD_WIDTH = const(320)
    LCD_HEIGHT = const(240)
    
    #MOSI is SDI, MISO is SDO
    def __init__(self, spi_id, sck, mosi, miso, rst, led, display_cs, touch_cs=None, orientation=0):
         
        # Pin setup
        self.rst = rst
        self.rst.init(mode = Pin.OUT)
        self.rst_enable()
        
        self.led = led
        self.led.init(mode = Pin.OUT)
        self.led_disable()
        
        self.display_cs = display_cs
        self.display_cs.init(mode = Pin.OUT)
        self.display_cs_disable()
        
        if touch_cs != None:
            self.touch_cs = touch_cs
            self.touch_cs.init(mode = Pin.OUT)
            self.touch_cs_disable()
        
        # SPI setup
        self.spi_id = spi_id
        self.sck = sck
        self.mosi = mosi
        self.miso = miso
        self.spi = SPI(spi_id, baudrate=DISPLAY_SPI_SPEED,
                       sck = self.sck,
                       mosi = self.mosi,
                       miso = self.miso)
        
        print(self.spi)
        
        self.reset()
        
        self.width = LCD_WIDTH
        self.height = LCD_HEIGHT
        self.orientation = orientation
        self.setOrientation(self.orientation)
        
        self.led_enable()
                
        #LVGL display and input driver connection
        try:
            global lv
            import lvgl as lv
        except ImportError:
            print("LVGL doesn't exist")
        
        print("Initializing lvgl")

        if not lv.is_initialized():
            lv.init()
        
        #Display driver connection
        self.disp_drv = lv.display_create(self.width, self.height)
        self.disp_drv.set_color_format(lv.COLOR_FORMAT.RGB565)
        self.pixel_size = 2
        self.buf_size = int(self.width * self.height * self.pixel_size / 10)
        self.buf1 = bytearray(self.buf_size)
        self.disp_drv.set_buffers(self.buf1, None, self.buf_size, lv.DISPLAY_RENDER_MODE.PARTIAL)
        self.disp_drv.set_flush_cb(self.flush_cb)

        #Touch screen driver connection
        self.indev_drv = lv.indev_create()
        self.indev_drv.set_type(lv.INDEV_TYPE.POINTER)
        self.indev_drv.set_display(self.disp_drv)
        self.indev_drv.set_read_cb(self.read_cb)
        

    """
        Helper functions for pin setup
    """
    def led_enable(self):
        self.led.high()
    
    def led_disable(self):
        self.led.low()
        
    def rst_enable(self):
        self.rst.low()
        
    def rst_disable(self):
        self.rst.high()
        
    def display_cs_enable(self):
        self.display_cs.low()
        
    def display_cs_disable(self):
        self.display_cs.high()
    
    def touch_cs_enable(self):
        self.touch_cs.low()
        
    def touch_cs_disable(self):
        self.touch_cs.high()


    def flush_cb(self, disp_drv, area, color_p):
        """
        Function used by LVGL to draw on display
        disp_drv - lvgl display driver
        area - struct with drawing area coordinates
        color_p - C_pointer to draw buffer (in little endian format)
        """
        size = (area.x2 - area.x1 + 1) * (area.y2 - area.y1 + 1)
        data_view = color_p.__dereference__(size * self.pixel_size)
        lv.draw_sw_rgb565_swap(data_view, size) #Swaps endianess of bytes in buffer from little to big
        self.set_area(area.x1, area.y1, area.x2, area.y2)
        self.draw_start()
        
        self.wr_buf_spi(data_view)
    
        self.draw_stop()

        self.disp_drv.flush_ready()


    def read_cb(self, indev_drv, data) -> int:
        """
        Function used by LVGL to poll touch screen controller
        indev_drv - lvgl input device driver
        data - reference to struct used to keep track of device reading (written to)
        """
        reading = self.touch_read()

        if(reading[0] == -1 and reading[1] == -1):
            data.state = lv.INDEV_STATE.RELEASED
            return False

        data.point.x = reading[0]
        data.point.y = reading[1]
        data.state = lv.INDEV_STATE.PRESSED
        return True

    def fill(self, color_rgb565):
        self.set_area(0, 0, self.height-1, self.width-1)
        self.draw_start()
        for i in range(self.width * self.height):
            self.draw(color_rgb565)
        self.draw_stop()
            
    def set_area(self, x0, y0, x1, y1):
        self.wr_cmd(COLUMN_ADDRESS_START_1, (x0>>0 & 0xFF)) 
        self.wr_cmd(COLUMN_ADDRESS_START_2, (x0>>8 & 0xFF))
        self.wr_cmd(COLUMN_ADDRESS_END_1, (x1>>0 & 0xFF)) 
        self.wr_cmd(COLUMN_ADDRESS_END_2, (x1>>8 & 0xFF))
        self.wr_cmd(ROW_ADDRESS_START_1, (y0>>0 & 0xFF)) 
        self.wr_cmd(ROW_ADDRESS_START_2, (y0>>8 & 0xFF)) 
        self.wr_cmd(ROW_ADDRESS_END_1, (y1>>0 & 0xFF)) 
        self.wr_cmd(ROW_ADDRESS_END_2, (y1>>8 & 0xFF)) 

    def draw_start(self):
        self.display_cs_enable()
        self.wr_spi(LCD_REGISTER)
        self.wr_spi(0x22)
        self.display_cs_disable()
        
        self.display_cs_enable()
        self.wr_spi(LCD_DATA)
        
    def draw_stop(self):
        self.display_cs_disable()
    

    def touch_read(self):
        """
        Return reading coordinates in the form of a (x, y) touple. If the touch screen is not 
        pressed the result will be (-1, -1)
        """
        if self.touch_cs != None:
            
            """
            New SPI configuration for touch screen controller, because the SPI bus is shared and 
            the display and touch don't support the same SPI speeds
            """
            self.spi = SPI(self.spi_id, baudrate = TOUCH_SPI_SPEED,
                          sck = self.sck,
                          mosi = self.mosi,
                          miso = self.miso)
            
            #get z data
            self.touch_cs_enable()

            self.wr_spi(ADS_CMD_START | ADS_CMD_8BIT | ADS_CMD_DIFF | ADS_CMD_Z1_POS | ADS_CMD_ALWAYS_ON)
            a1 = self.rd_spi(1)&0x7F
            self.wr_spi(ADS_CMD_START | ADS_CMD_8BIT | ADS_CMD_DIFF | ADS_CMD_Z2_POS | ADS_CMD_ALWAYS_ON)
            a2 = (255-self.rd_spi(1))&0x7F
            
            self.touch_cs_disable()
            pressure = a1 + a2

            x_raw = -1
            y_raw = -1
            x = -1
            y = -1
            if(pressure < MIN_PRESSURE):
                return (x, y)

            self.touch_cs_enable()
            
            #get x data, two times for confidence
            self.wr_spi(ADS_CMD_START | ADS_CMD_12BIT | ADS_CMD_DIFF | ADS_CMD_X_POS | ADS_CMD_ALWAYS_ON)
            a1 = self.rd_spi(2)
            self.wr_spi(ADS_CMD_START | ADS_CMD_12BIT | ADS_CMD_DIFF | ADS_CMD_X_POS | ADS_CMD_ALWAYS_ON)
            a2 = self.rd_spi(2)
            
            #Two bytes are read but needed information is in bits [14:3], consult datasheet for more info
            x_raw = (a2>>3) 

            #get y data, two times for confidence
            self.wr_spi(ADS_CMD_START | ADS_CMD_12BIT | ADS_CMD_DIFF | ADS_CMD_Y_POS | ADS_CMD_ALWAYS_ON)
            a1 = self.rd_spi(2)
            self.wr_spi(ADS_CMD_START | ADS_CMD_12BIT | ADS_CMD_DIFF | ADS_CMD_Y_POS | ADS_CMD_ALWAYS_ON)
            a2 = self.rd_spi(2)

            #Same reading procedure as for x_raw
            y_raw = (a2>>3) 
            
            """
            By default the touch controller has different orientation of x and y axis than LVGL.
            For this reason we have to map it differently. Keep in mind such orientation 
            will be used even when LVGL is not used.
            """
            if(self.orientation == 0):
                x = self.map_touch(x_raw, X_MIN, X_MAX, 0, LCD_HEIGHT-1)
                y = self.map_touch(y_raw, Y_MIN, Y_MAX, 0, LCD_WIDTH-1)
            elif(self.orientation == 90):
                x = self.map_touch(4095-y_raw, Y_MIN, Y_MAX, 0, LCD_WIDTH-1)
                y = self.map_touch(x_raw, X_MIN, X_MAX, 0, LCD_HEIGHT-1)
            elif(self.orientation == 180):
                x = self.map_touch(4095-x_raw, X_MIN, X_MAX, 0, LCD_HEIGHT-1)
                y = self.map_touch(4095-y_raw, Y_MIN, Y_MAX, 0, LCD_WIDTH-1)
            elif(self.orientation == 270):
                x = self.map_touch(y_raw, Y_MIN, Y_MAX, 0, LCD_WIDTH-1)
                y = self.map_touch(4095-x_raw, X_MIN, X_MAX, 0, LCD_HEIGHT-1)


            self.touch_cs_disable()
            
            #Returning SPI configuration to that for display
            self.spi = SPI(self.spi_id, baudrate=DISPLAY_SPI_SPEED,
                          sck = self.sck,
                          mosi = self.mosi,
                          miso = self.miso)
            
            return (x, y) 
    
    def setOrientation(self, orientation):
        if(orientation == 0):
            self.wr_cmd(MEMORY_ACCESS_CONTROL, 0x08) 
            self.width = LCD_HEIGHT
            self.height = LCD_WIDTH
        elif(orientation == 90):
            self.wr_cmd(MEMORY_ACCESS_CONTROL, 0xA8) 
            self.width = LCD_WIDTH
            self.height = LCD_HEIGHT
        elif(orientation == 180):
            self.wr_cmd(MEMORY_ACCESS_CONTROL, 0xC8) 
            self.width = LCD_HEIGHT
            self.height = LCD_WIDTH
        elif(orientation == 270):
            self.wr_cmd(MEMORY_ACCESS_CONTROL, 0x68) 
            self.width = LCD_WIDTH
            self.height = LCD_HEIGHT
        else:
            raise ValueError("Orientation can only be 0, 90, 180 and 270")
        self.orientation = orientation
    
    def reset(self):
        self.display_cs_disable()
        
        self.rst_enable()
        time.sleep_ms(50)
        self.rst_disable()
        time.sleep_ms(120)

        #Initial setup commands
        
        #driving ability
        self.wr_cmd(POWER_CONTROL_INTERNAL_USE_1, 0x00) 
        self.wr_cmd(POWER_CONTROL_INTERNAL_USE_2, 0x20) 
        self.wr_cmd(SOURCE_CONTROL_INTERNAL_USE_1, 0x0C) 
        self.wr_cmd(SOURCE_CONTROL_INTERNAL_USE_2, 0xC4) 
        self.wr_cmd(SOURCE_OP_CONTROL_NORMAL, 0x40) 
        self.wr_cmd(SOURCE_OP_CONTROL_IDLE, 0x38) 
        self.wr_cmd(0xF1, 0x01) 
        self.wr_cmd(0xF2, 0x10) 
        self.wr_cmd(DISPLAY_CONTROL_2, 0xA3)
        #power voltage
        self.wr_cmd(POWER_CONTROL_2, 0x1B)
        self.wr_cmd(POWER_CONTROL_1, 0x01)
        self.wr_cmd(VCOM_CONTROL_2, 0x2F)
        self.wr_cmd(VCOM_CONTROL_3, 0x57)
        #VCOM offset
        self.wr_cmd(VCOM_CONTROL_1, 0x8D)
        #power on
        self.wr_cmd(OSC_CONTROL_2, 0x36)
        #start osc
        self.wr_cmd(OSC_CONTROL_1, 0x01)
        #wakeup
        self.wr_cmd(DISPLAY_MODE_CONTROL, 0x00)
        self.wr_cmd(POWER_CONTROL_6, 0x88)
        time.sleep_ms(5)
        self.wr_cmd(POWER_CONTROL_6, 0x80)
        time.sleep_ms(5)
        self.wr_cmd(POWER_CONTROL_6, 0x90)
        time.sleep_ms(5)
        self.wr_cmd(POWER_CONTROL_6, 0xD0)
        time.sleep_ms(5)
        #color selection
        self.wr_cmd(COLMOD, 0x05) #0x05=65k, 0x06=262k
        #panel characteristic
        self.wr_cmd(PANEL_CHARACTERISTIC, 0x00)
        #display options
        self.wr_cmd(MEMORY_ACCESS_CONTROL, 0xA8) # 0xA8 RGB, 0xA0 BGR (even though datasheet says otherwise)
        self.wr_cmd(COLUMN_ADDRESS_START_1, 0x00) #x0
        self.wr_cmd(COLUMN_ADDRESS_START_2, 0x00) #x0
        self.wr_cmd(COLUMN_ADDRESS_END_1, ((LCD_WIDTH-1)>>0)&0xFF)
        self.wr_cmd(COLUMN_ADDRESS_END_2, ((LCD_WIDTH-1)>>8)&0xFF)
        self.wr_cmd(ROW_ADDRESS_START_1, 0x00) #y0
        self.wr_cmd(ROW_ADDRESS_START_2, 0x00) #y0
        self.wr_cmd(ROW_ADDRESS_END_1, ((LCD_HEIGHT-1)>>0)&0xFF)
        self.wr_cmd(ROW_ADDRESS_END_2, ((LCD_HEIGHT-1)>>8)&0xFF)
        #display on
        self.wr_cmd(DISPLAY_CONTROL_3, 0x38)
        time.sleep_ms(50)
        self.wr_cmd(DISPLAY_CONTROL_3, 0x3C)
        time.sleep_ms(5)
        
    def wr_cmd(self, cmd, param):
       self.display_cs_enable();
       self.wr_spi(LCD_REGISTER);
       self.wr_spi(cmd);
       self.display_cs_disable();

       self.display_cs_enable();
       self.wr_spi(LCD_DATA);
       self.wr_spi(param);
       self.display_cs_disable();

    def rd_spi(self, num_of_bytes):
        #reads bytes from SPI in big endian format
        return int.from_bytes(self.spi.read(num_of_bytes), "big")

    def wr_spi(self, data):
        #important that data is wrapped with []
        self.spi.write(bytes([data]))
        
    def wr_buf_spi(self, buf):
        self.spi.write(buf)

    def map_touch(self, value, min_value_in, max_value_in, min_value_out, max_value_out):
        return int((value - min_value_in) * (max_value_out - min_value_out) / (max_value_in - min_value_in) + min_value_out)

