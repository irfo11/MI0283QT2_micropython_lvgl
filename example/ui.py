import lvgl as lv
from machine import Pin, ADC, Timer, PWM
from micropython import const


def map(val, in_min, in_max, out_min, out_max):
      return int((val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

SCREEN_TRANSITION_TIME = const(30)

#Shorter transition for buttons
btn_short_trans_props = [lv.STYLE.BG_COLOR, lv.STYLE.BORDER_COLOR, lv.STYLE.BORDER_WIDTH,
                         lv.STYLE.TRANSFORM_WIDTH, lv.STYLE.TRANSFORM_HEIGHT, 0]
btn_short_trans = lv.style_transition_dsc_t()
btn_short_trans.init(btn_short_trans_props, lv.anim_t.path_ease_out, 10, 0, None)

#################STYLE FOR MOST BUTTONS#################
btn_default = lv.style_t()
btn_default.init()
btn_default.set_transition(btn_short_trans)
btn_default.set_bg_color(lv.palette_main(lv.PALETTE.BLUE))
btn_default.set_border_color(lv.color_black())
btn_default.set_border_width(2)
#btn_default.set_radius(0)

btn_press = lv.style_t()
btn_press.init()
btn_press.set_transition(btn_short_trans)
btn_press.set_bg_color(lv.palette_darken(lv.PALETTE.BLUE, 2))
btn_press.set_bg_opa(255)
##########################################################

#################STYLE FOR HOME BUTTON####################
home_btn_default = lv.style_t()
home_btn_default.init()
home_btn_default.set_transition(btn_short_trans)
home_btn_default.set_bg_color(lv.color_hex3(0xfff))
home_btn_default.set_border_width(0)
home_btn_default.set_shadow_width(0)

home_btn_pressed = lv.style_t()
home_btn_pressed.init()
home_btn_pressed.set_transition(btn_short_trans) 
home_btn_pressed.set_bg_color(lv.palette_lighten(lv.PALETTE.GREY, 3))
##########################################################


class labeled_button:
    def __init__(self, parent, label_text, default_state_style=None,
                 pressed_state_style=None, label_text_color=lv.color_hex3(0xfff)):
        self.button = lv.button(parent)
        if(default_state_style != None):
            self.button.add_style(default_state_style, lv.PART.MAIN | lv.STATE.DEFAULT)
        if(pressed_state_style != None):
            self.button.add_style(pressed_state_style, lv.PART.MAIN | lv.STATE.PRESSED)
        self.label = lv.label(self.button)
        self.label.set_text(label_text)
        self.label.align(lv.ALIGN.CENTER, 0, 0)
        self.label.set_style_text_color(label_text_color, 0)

class screen_with_home_button:

    def __init__(self, parent=None, home_screen=None):
        
        column_desc = [lv.grid_fr(1), lv.GRID_TEMPLATE_LAST]
        row_desc = [lv.grid_fr(1), 20, lv.GRID_TEMPLATE_LAST]
        self.screen = lv.obj(parent)
        self.screen.set_grid_dsc_array(column_desc, row_desc)
        self.screen.set_layout(lv.LAYOUT.GRID)
        
        #styles to fill the entire screen
        self.screen.set_style_pad_column(0, lv.PART.MAIN)
        self.screen.set_style_pad_row(5, lv.PART.MAIN)
        self.screen.set_style_pad_top(0, 0)
        self.screen.set_style_pad_bottom(5, 0)
        self.screen.set_style_pad_left(0, 0)
        self.screen.set_style_pad_right(0, 0)

        self.home_button = labeled_button(self.screen, lv.SYMBOL.HOME, home_btn_default, 
                                          home_btn_pressed, lv.color_black())
        self.home_button.label.set_style_text_color(lv.color_black(), 0)
        self.home_button.button.set_style_height(20, 0)
        self.home_button.button.set_grid_cell(lv.GRID_ALIGN.CENTER, 0, 1, lv.GRID_ALIGN.END, 1, 1)

        #container so child classes can easily put objects
        self.main_area_cont = lv.obj(self.screen)
        self.main_area_cont.set_grid_cell(lv.GRID_ALIGN.STRETCH, 0, 1, lv.GRID_ALIGN.STRETCH, 0, 1)
        self.main_area_cont.set_style_border_width(0, 0)
        self.main_area_cont.set_style_pad_top(0, 0)
        self.main_area_cont.set_style_pad_bottom(0, 0)
        self.main_area_cont.set_style_pad_left(0, 0)
        self.main_area_cont.set_style_pad_right(0, 0)

        self.home_screen = home_screen
        self.home_button.button.add_event_cb(self.change_to_home, lv.EVENT.CLICKED, None)
    
    def change_to_home(self, event):
        if(self.home_screen != None):
            lv.screen_load_anim(self.home_screen, lv.SCR_LOAD_ANIM.OVER_TOP, SCREEN_TRANSITION_TIME, 0, True)

class home_screen(screen_with_home_button):

    def __init__(self, leds, analog_pin, parent=None, home_screen=None):
        super().__init__(parent, home_screen)

        self.leds = leds
        self.analog_pin = analog_pin

        self.btn_map = ["Led\nControl", "Analog\nReading", "Graphing", "\n", "Analog\nWriting", "Password\nScreen", lv.SYMBOL.SETTINGS, ""]
        self.btn_mat = lv.buttonmatrix(self.main_area_cont)
        self.btn_mat.set_map(self.btn_map)
        self.btn_mat.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.ITEMS)
        self.btn_mat.set_style_bg_color(lv.palette_lighten(lv.PALETTE.BLUE, 2), lv.PART.ITEMS)
        self.btn_mat.align(lv.ALIGN.CENTER, 0, 0)
        self.btn_mat.set_style_border_width(0, 0)
        self.btn_mat.set_style_pad_top(0, 0)
        self.btn_mat.set_style_pad_bottom(0, 0)
        self.btn_mat.set_style_pad_right(0, 0)
        self.btn_mat.set_style_pad_left(0, 0)
        self.btn_mat.set_style_size(300, 190, 0)


        self.btn_mat.add_event_cb(self.btn_mat_clicked, lv.EVENT.VALUE_CHANGED, None)

        lv.screen_load(self.screen)

    def btn_mat_clicked(self, event):
        btn_id = self.btn_mat.get_selected_button()
        scr_to_load = None

        #The reason for not putting scr_to_load.show_screen() outside of the
        #ifs, is because scr_to_load doesn't need to implement it. It could have another name or use parameters,
        #here is all the same for simplicity
        if(btn_id == 0): #Led Control
            scr_to_load = led_control_screen(None, self.screen, self.leds)
            scr_to_load.show_screen()
        elif(btn_id == 1): #Analaog Reading
            scr_to_load = analog_reading_screen(None, self.screen, self.analog_pin)
            scr_to_load.show_screen()
        elif(btn_id == 2): #Graphing
            scr_to_load = graphing_screen(None, self.screen, self.analog_pin)
            scr_to_load.show_screen()
        elif(btn_id == 3): #Analog Writing
            scr_to_load = analog_writing_screen(None, self.screen, self.leds)
            scr_to_load.show_screen()
        elif(btn_id == 4): #Password screen
            scr_to_load = password_screen(None, self.screen)
            scr_to_load.show_screen()
        elif(btn_id == 5): #Settings screen
            scr_to_load = settings_screen(None, self.screen)
            scr_to_load.show_screen()

class led_control_screen(screen_with_home_button):

    def __init__(self, parent, home_screen, leds):
        super().__init__(parent, home_screen)
        self.leds=leds
        for led in self.leds:
            led.init(mode=Pin.OUT)

        self.screen.add_event_cb(self.leds_to_input, lv.EVENT.DELETE, None)

        self.main_area_cont.set_layout(lv.LAYOUT.GRID)
        led_control_col_dsc = [lv.grid_fr(1), lv.grid_fr(1), lv.grid_fr(1), lv.grid_fr(1), lv.GRID_TEMPLATE_LAST]
        led_control_row_dsc = [lv.grid_fr(1), lv.grid_fr(1), lv.grid_fr(1), lv.GRID_TEMPLATE_LAST]
        self.main_area_cont.set_grid_dsc_array(led_control_col_dsc, led_control_row_dsc)

        self.led0_switch = lv.switch(self.main_area_cont)
        self.led1_switch = lv.switch(self.main_area_cont)
        self.led2_switch = lv.switch(self.main_area_cont)
        self.led3_switch = lv.switch(self.main_area_cont)
        self.led0_switch.set_grid_cell(lv.GRID_ALIGN.CENTER, 0, 1, lv.GRID_ALIGN.END, 0, 1)
        self.led1_switch.set_grid_cell(lv.GRID_ALIGN.CENTER, 1, 1, lv.GRID_ALIGN.END, 0, 1)
        self.led2_switch.set_grid_cell(lv.GRID_ALIGN.CENTER, 2, 1, lv.GRID_ALIGN.END, 0, 1)
        self.led3_switch.set_grid_cell(lv.GRID_ALIGN.CENTER, 3, 1, lv.GRID_ALIGN.END, 0, 1)

        self.led0_label = lv.label(self.main_area_cont)
        self.led1_label = lv.label(self.main_area_cont)
        self.led2_label = lv.label(self.main_area_cont)
        self.led3_label = lv.label(self.main_area_cont)
        self.led0_label.add_flag(lv.obj.FLAG.IGNORE_LAYOUT)
        self.led1_label.add_flag(lv.obj.FLAG.IGNORE_LAYOUT)
        self.led2_label.add_flag(lv.obj.FLAG.IGNORE_LAYOUT)
        self.led3_label.add_flag(lv.obj.FLAG.IGNORE_LAYOUT)
        self.led0_label.set_text("LED0")
        self.led1_label.set_text("LED1")
        self.led2_label.set_text("LED2")
        self.led3_label.set_text("LED3")
        self.led0_label.align_to(self.led0_switch, lv.ALIGN.OUT_TOP_MID, 0, 0)
        self.led1_label.align_to(self.led1_switch, lv.ALIGN.OUT_TOP_MID, 0, 0)
        self.led2_label.align_to(self.led2_switch, lv.ALIGN.OUT_TOP_MID, 0, 0)
        self.led3_label.align_to(self.led3_switch, lv.ALIGN.OUT_TOP_MID, 0, 0)

        self.led_dropdown = lv.dropdown(self.main_area_cont)
        self.led_dropdown.set_options("None\nLED4\nLED5")
        self.led_dropdown.set_grid_cell(lv.GRID_ALIGN.CENTER, 1, 2, lv.GRID_ALIGN.CENTER, 1, 1)

        self.led_roller = lv.roller(self.main_area_cont)
        self.led_roller.set_options("None\nLED6\nLED7", lv.roller.MODE.NORMAL)
        self.led_roller.set_visible_row_count(2)
        self.led_roller.set_grid_cell(lv.GRID_ALIGN.CENTER, 1, 2, lv.GRID_ALIGN.END, 2, 1)

        self.led0_switch.add_event_cb(self.led0_switch_changed, lv.EVENT.VALUE_CHANGED, None)
        self.led1_switch.add_event_cb(self.led1_switch_changed, lv.EVENT.VALUE_CHANGED, None)
        self.led2_switch.add_event_cb(self.led2_switch_changed, lv.EVENT.VALUE_CHANGED, None)
        self.led3_switch.add_event_cb(self.led3_switch_changed, lv.EVENT.VALUE_CHANGED, None)

        self.led_dropdown.add_event_cb(self.led_dropdown_new_select, lv.EVENT.VALUE_CHANGED, None)

        self.led_roller.add_event_cb(self.led_roller_new_select, lv.EVENT.VALUE_CHANGED, None)

    def show_screen(self):
        lv.screen_load_anim(self.screen, lv.SCR_LOAD_ANIM.OVER_BOTTOM, SCREEN_TRANSITION_TIME, 0, False)

    def led0_switch_changed(self, event):
        led_switch_value = 1 if self.led0_switch.has_state(lv.STATE.CHECKED) else 0
        self.leds[0].value(led_switch_value) 
    def led1_switch_changed(self, event):
        led_switch_value = 1 if self.led1_switch.has_state(lv.STATE.CHECKED) else 0
        self.leds[1].value(led_switch_value) 
    def led2_switch_changed(self, event):
        led_switch_value = 1 if self.led2_switch.has_state(lv.STATE.CHECKED) else 0
        self.leds[2].value(led_switch_value) 
    def led3_switch_changed(self, event):
        led_switch_value = 1 if self.led3_switch.has_state(lv.STATE.CHECKED) else 0
        self.leds[3].value(led_switch_value) 

    def led_dropdown_new_select(self, event):
        led_dropdown_selection = self.led_dropdown.get_selected()
        if(led_dropdown_selection == 0):
            self.leds[4].off()
            self.leds[5].off()
        elif(led_dropdown_selection == 1):
            self.leds[4].on()
            self.leds[5].off()
        elif(led_dropdown_selection == 2):
            self.leds[4].off()
            self.leds[5].on()
    def led_roller_new_select(self, event):
        led_roller_selection = self.led_roller.get_selected()
        if(led_roller_selection == 0):
            self.leds[6].off()
            self.leds[7].off()
        elif(led_roller_selection == 1):
            self.leds[6].on()
            self.leds[7].off()
        elif(led_roller_selection == 2):
            self.leds[6].off()
            self.leds[7].on()

    def leds_to_input(self, event):
        for led in self.leds:
            led.low()
            led.init(Pin.IN)
        

class analog_reading_screen(screen_with_home_button):

    def __init__(self, parent, home_screen, sensor):
        super().__init__(parent, home_screen) 
        self.sensor = sensor
        self.screen.add_event_cb(self.clean_up, lv.EVENT.DELETE, None)

        self.pressure_scale = lv.scale(self.main_area_cont)
        self.pressure_scale.set_size(150, 150)
        self.pressure_scale.align(lv.ALIGN.CENTER, 0, 10)
        self.pressure_scale.set_mode(lv.scale.MODE.ROUND_OUTER)
        self.pressure_scale.set_style_radius(lv.RADIUS_CIRCLE, 0)
        self.pressure_scale.set_total_tick_count(51)
        self.pressure_scale.set_major_tick_every(5)
        self.pressure_scale.set_style_length(5, lv.PART.ITEMS)
        self.pressure_scale.set_style_length(10, lv.PART.INDICATOR)
        self.pressure_scale.set_range(0, 20)
        self.pressure_scale.set_angle_range(270)
        self.pressure_scale.set_rotation(135)

        self.pressure_scale_label = lv.label(self.pressure_scale)
        self.pressure_scale_label.set_text("BAR")
        self.pressure_scale_label.set_style_text_color(lv.color_black(), 0)
        self.pressure_scale_label.align_to(self.pressure_scale, lv.ALIGN.TOP_MID, 0, 30)

        self.needle_line = lv.line(self.pressure_scale)
        self.needle_line.set_style_line_width(6, lv.PART.MAIN)
        self.needle_line.set_style_line_rounded(True, lv.PART.MAIN)

        self.pressure_scale.set_line_needle_value(self.needle_line, 60, 0)

        sec_style = lv.style_t()
        sec_style.init()
        sec_style.set_arc_color(lv.palette_main(lv.PALETTE.GREEN))
        sec_style.set_arc_width(5)
        sec = self.pressure_scale.add_section()
        sec.set_range(0, 12)
        sec.set_style(0, sec_style)

        sec_style = lv.style_t()
        sec_style.init()
        sec_style.set_arc_color(lv.palette_main(lv.PALETTE.YELLOW))
        sec_style.set_arc_width(5)
        sec = self.pressure_scale.add_section()
        sec.set_range(12, 18)
        sec.set_style(0, sec_style)

        sec_style = lv.style_t()
        sec_style.init()
        sec_style.set_arc_color(lv.palette_main(lv.PALETTE.RED))
        sec_style.set_arc_width(5)
        sec = self.pressure_scale.add_section()
        sec.set_range(18, 20)
        sec.set_style(0, sec_style)

        self.timer = Timer(mode=Timer.PERIODIC, period=40, callback=self.update_scale)
        

    def show_screen(self):
        lv.screen_load_anim(self.screen, lv.SCR_LOAD_ANIM.OVER_BOTTOM, SCREEN_TRANSITION_TIME, 0, False)

    def update_scale(self, timer):
        sensor_reading = self.sensor.read_u16()
        sensor_reading = map(sensor_reading, 0, 65535, 0, 20)
        self.pressure_scale.set_line_needle_value(self.needle_line, 60, sensor_reading)

    def clean_up(self, event):
        self.timer.deinit()
        
class graphing_screen(screen_with_home_button):

    def __init__(self, parent, home_screen, sensor):
        super().__init__(parent, home_screen)
        self.sensor = sensor
        self.screen.add_event_cb(self.clean_up, lv.EVENT.DELETE, None)

        self.graph = lv.chart(self.main_area_cont)
        self.graph.set_style_width(250, 0)
        self.graph.set_style_height(200, 0)
        self.graph.align(lv.ALIGN.CENTER, 0, 0)
        self.graph.set_type(lv.chart.TYPE.LINE)
        self.graph.set_div_line_count(10, 10)

        self.graph_series = self.graph.add_series(lv.color_black(), lv.chart.AXIS.PRIMARY_Y)
        self.graph.set_point_count(30)
        self.graph.set_all_value(self.graph_series, 0) #all values 0 at the beginning
        self.graph.set_range(lv.chart.AXIS.PRIMARY_Y, 0, 10)
        self.graph.set_update_mode(lv.chart.UPDATE_MODE.SHIFT)

        self.y_axis = lv.scale(self.main_area_cont)
        self.y_axis.set_mode(lv.scale.MODE.VERTICAL_LEFT)
        self.y_axis.align_to(self.graph, lv.ALIGN.OUT_LEFT_MID, 0, -25)
        self.y_axis.set_style_height(180, 0)
        self.y_axis.set_range(0, 10)
        self.y_axis.set_total_tick_count(19);
        self.y_axis.set_major_tick_every(2);
        self.y_axis.set_style_length(5, lv.PART.ITEMS)
        self.y_axis.set_style_length(10, lv.PART.INDICATOR)
        
        self.time_division_label = lv.label(self.main_area_cont)
        self.time_division_label.set_text("Sample time = 500ms")
        self.time_division_label.align_to(self.graph, lv.ALIGN.TOP_MID, 0, 0)

        self.timer = Timer(mode=Timer.PERIODIC, period=500, callback=self.update_graph)

    def show_screen(self):
        lv.screen_load_anim(self.screen, lv.SCR_LOAD_ANIM.OVER_BOTTOM, SCREEN_TRANSITION_TIME, 0, False)
    
    def update_graph(self, event):
        val = map(self.sensor.read_u16(), 0, 65535, 0, 10)
        self.graph.set_next_value(self.graph_series, val)

    def clean_up(self, event):
        self.timer.deinit()

class analog_writing_screen(screen_with_home_button):

    def __init__(self, parent, home_screen, leds):
        super().__init__(parent, home_screen)
        self.leds = list(leds[0:7])
        for led in self.leds:
            led.init(mode=Pin.OUT)
        self.pwm_pin = PWM(leds[7])
        self.pwm_pin.freq(100)

        self.screen.add_event_cb(self.clean_up, lv.EVENT.DELETE, None)
        self.main_area_cont.set_layout(lv.LAYOUT.GRID)
        analog_writing_col_dsc = [lv.grid_fr(1), lv.GRID_TEMPLATE_LAST]
        analog_writing_row_dsc = [lv.grid_fr(1), lv.grid_fr(1), lv.GRID_TEMPLATE_LAST]
        self.main_area_cont.set_grid_dsc_array(analog_writing_col_dsc, analog_writing_row_dsc)

        self.led_slider = lv.slider(self.main_area_cont)
        self.led_slider.set_range(0, 7)
        self.led_slider.set_grid_cell(lv.GRID_ALIGN.CENTER, 0, 1, lv.GRID_ALIGN.CENTER, 0, 1)

        self.led_spinbox = lv.spinbox(self.main_area_cont)
        self.led_spinbox_min_val = 0
        self.led_spinbox_max_val = 1000
        self.led_spinbox.set_range(self.led_spinbox_min_val, self.led_spinbox_max_val)
        self.led_spinbox.set_digit_format(3, 0)
        self.led_spinbox.set_rollover(False)
        self.led_spinbox.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN)
        self.led_spinbox.set_style_text_font(lv.font_montserrat_24, 0)
        self.led_spinbox.set_style_width(80, 0)
        self.led_spinbox.set_style_height(55, 0)
        self.led_spinbox.set_grid_cell(lv.GRID_ALIGN.CENTER, 0, 1, lv.GRID_ALIGN.CENTER, 1, 1)

        self.led_slider_label = lv.label(self.main_area_cont)
        self.led_slider_label.set_text("LED0-6 Control")
        self.led_slider_label.add_flag(lv.obj.FLAG.IGNORE_LAYOUT) #ignores grid layout, so it can be set wherever
        self.led_slider_label.align_to(self.led_slider, lv.ALIGN.OUT_TOP_MID, 0, -15)

        self.led_spinbox_label = lv.label(self.main_area_cont)
        self.led_spinbox_label.set_text("LED7 PWM Control")
        self.led_spinbox_label.add_flag(lv.obj.FLAG.IGNORE_LAYOUT)
        self.led_spinbox_label.align_to(self.led_spinbox, lv.ALIGN.OUT_TOP_MID, 0, -15)

        self.plus_button = labeled_button(self.main_area_cont, lv.SYMBOL.PLUS, btn_default, btn_press)
        self.minus_button = labeled_button(self.main_area_cont, lv.SYMBOL.MINUS, btn_default, btn_press)
        self.plus_button.button.add_flag(lv.obj.FLAG.IGNORE_LAYOUT)
        self.minus_button.button.add_flag(lv.obj.FLAG.IGNORE_LAYOUT)
        self.plus_button.button.set_style_width(50, 0)
        self.plus_button.button.set_style_height(50, 0)
        self.minus_button.button.set_style_width(50, 0)
        self.minus_button.button.set_style_height(50, 0)
        self.plus_button.button.align_to(self.led_spinbox, lv.ALIGN.OUT_RIGHT_MID, 5, 0)
        self.minus_button.button.align_to(self.led_spinbox, lv.ALIGN.OUT_LEFT_MID, -5, 0)


        self.led_slider.add_event_cb(self.led_slider_changed, lv.EVENT.VALUE_CHANGED, None)
        self.plus_button.button.add_event_cb(self.increase_led_spinbox, lv.EVENT.CLICKED, None)
        self.minus_button.button.add_event_cb(self.decrease_led_spinbox, lv.EVENT.CLICKED, None)
        self.led_spinbox.add_event_cb(self.led_spinbox_changed, lv.EVENT.VALUE_CHANGED, None)

    def show_screen(self):
        lv.screen_load_anim(self.screen, lv.SCR_LOAD_ANIM.OVER_BOTTOM, SCREEN_TRANSITION_TIME, 0, False)

    def led_slider_changed(self, event):
        leds_on = self.led_slider.get_value() # +1 for range function
        for i in range(0, leds_on):
            self.leds[i].high()
        for i in range(leds_on, 7):
            self.leds[i].low()

    def increase_led_spinbox(self, event):
        self.led_spinbox.increment()
    
    def decrease_led_spinbox(self, event):
        self.led_spinbox.decrement()
    
    def led_spinbox_changed(self, event):
        pwm_val = map(self.led_spinbox.get_value(), 0, 1000, 0, 65535)
        self.pwm_pin.duty_u16(pwm_val)

    def clean_up(self, event):
        self.pwm_pin.deinit()
        for led in self.leds:
            led.low()
            led.init(mode=Pin.IN)

class password_screen(screen_with_home_button):

    def __init__(self, parent, home_screen):
        super().__init__(parent, home_screen)

        self.keyboard = lv.keyboard(self.main_area_cont)

        self.password_textarea = lv.textarea(self.main_area_cont)
        self.password_textarea.align_to(self.keyboard, lv.ALIGN.OUT_TOP_MID, 0, 50)
        self.password_textarea.set_style_height(40, 0)
        self.password_textarea.set_placeholder_text("Password")
        self.password_textarea.set_password_mode(True)

        self.keyboard.set_textarea(self.password_textarea)
        
        self.keyboard.add_event_cb(self.test_password, lv.EVENT.READY, None)

    def show_screen(self):
        lv.screen_load_anim(self.screen, lv.SCR_LOAD_ANIM.OVER_BOTTOM, SCREEN_TRANSITION_TIME, 0, False)

    def test_password(self, event):
        password = "embedded"
        msgbox = lv.msgbox(None)
        msgbox.add_title("Info")
        msgbox.add_close_button()
        ok_button = msgbox.add_footer_button("Ok")
        #example with lambda function
        ok_button.add_event_cb(lambda event : msgbox.close(), lv.EVENT.CLICKED, None)
        if(self.password_textarea.get_text() == password):
            msgbox.add_text("Password is correct")
        else:
            msgbox.add_text("Password is incorrect")

class settings_screen(screen_with_home_button):

    def __init__(self, parent, home_screen):
        super().__init__(parent, home_screen)
        
        self.screen.remove_flag(lv.obj.FLAG.SCROLLABLE)
        
        self.menu = lv.menu(self.main_area_cont)
        self.menu.remove_flag(lv.obj.FLAG.SCROLLABLE)
        self.menu.set_style_width(300, 0)
        self.menu.set_style_height(200, 0)

        #wifi subpage
        self.wifi_page = lv.menu_page(self.menu, None)
        self.wifi_cont = lv.menu_cont(self.wifi_page)
        self.wifi_switch_label = lv.label(self.wifi_cont)
        self.wifi_switch_label.set_text("Wi-Fi")
        self.wifi_switch = lv.switch(self.wifi_cont)
        
        #brightness subpage
        self.brightness_page = lv.menu_page(self.menu, None)
        self.brightness_cont = lv.menu_cont(self.brightness_page)
        self.brightness_slider_label = lv.label(self.brightness_cont)
        self.brightness_slider_label.set_text("Brightness  ")
        self.brightness_slider = lv.slider(self.brightness_cont)
        self.brightness_slider.set_style_width(110, 0)

        #info page
        self.info_page = lv.menu_page(self.menu, None)
        self.info_cont = lv.menu_cont(self.info_page)
        self.system_info_label = lv.label(self.info_cont)
        self.system_info_label.set_text("LVGL v9 \nMicropython v1.20 \nRaspberry Pi Pico W \n\nThat's all you need to know (o_o)/")

        #main page
        self.main_page = lv.menu_page(self.menu, "Settings")
        self.main_page.remove_flag(lv.obj.FLAG.SCROLLABLE)

        self.main_wifi_cont = lv.menu_cont(self.main_page)
        self.wifi_label = lv.label(self.main_wifi_cont)
        self.wifi_label.set_text(lv.SYMBOL.WIFI+" Wi-Fi")
        self.menu.set_load_page_event(self.main_wifi_cont, self.wifi_page)

        self.main_brightness_cont = lv.menu_cont(self.main_page)
        self.brightness_label = lv.label(self.main_brightness_cont)
        self.brightness_label.set_text(lv.SYMBOL.EYE_OPEN+" Brightness")
        self.menu.set_load_page_event(self.main_brightness_cont, self.brightness_page)

        self.main_about_cont = lv.menu_cont(self.main_page)
        self.about_label = lv.label(self.main_about_cont)
        self.about_label.set_text("About")
        self.menu.set_load_page_event(self.main_about_cont, self.info_page)


        self.menu.set_page(self.main_page)
    
    def show_screen(self):
        lv.screen_load_anim(self.screen, lv.SCR_LOAD_ANIM.OVER_BOTTOM, SCREEN_TRANSITION_TIME, 0, False)



