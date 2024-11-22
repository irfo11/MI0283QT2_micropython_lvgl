import lvgl as lv
import ui
from MI0283QT2_lvgl import *

from machine import Timer, ADC

"""
Everytime you want to run this program, restart your board
"""
def lv_tick_inc(timer):
    lv.tick_inc(5) #time should be the same as the period of the timer

def lv_timer_handler(timer):
    lv.timer_handler()

disp = MI0283QT2_lvgl(spi_id = 0,
				 sck = Pin(18), 
				 mosi = Pin(19), 
				 miso = Pin(16), 
				 rst = Pin(20), 
				 led = Pin(21), 
				 display_cs = Pin(17), 
				 touch_cs=Pin(22), 
				 orientation=270)

tick_timer = Timer(mode=Timer.PERIODIC, period=5, callback=lv_tick_inc)
handler_timer = Timer(mode=Timer.PERIODIC, period=15, callback=lv_timer_handler)

leds = [Pin(4), Pin(5), Pin(6), Pin(7), Pin(8), Pin(9), Pin(10), Pin(11)]
analog_pin = ADC(Pin(28))

scr_home = ui.home_screen(leds, analog_pin)

#When running in Thonny on Raspberry Pi Pico it gives a backend error, but it should work without the loop as well
while True:
    pass
