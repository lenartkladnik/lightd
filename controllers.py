from machine import Pin, Timer
import time

def gpio_send_press(pin, duration_ms):
    pin.init(Pin.OUT)
    pin.value(0)
    time.sleep_ms(duration_ms)
    pin.init(Pin.IN)

def clamp(n: int, from_to: range):
    return max(from_to[0], min(n, from_to[-1]))

class LightsStatus:
    def __init__(self, brightness_level: int, brightness_range: range, color_level: int, color_range: range, on: bool = True) -> None:
        self.brightness_level: int = brightness_level
        self.brightness_range: range = brightness_range
        self.color_level: int = color_level
        self.color_range: range = color_range
        self.on: bool = on

    def change_brightness(self, n: int):
        if self.on:
            self.brightness_level += n

    def change_color(self, n: int):
        if self.on:
            self.color_level += n

class BilresaController:
    '''
    IKEA Bilresa controller
    '''

    def __init__(self, button_up_pin: int, button_down_pin: int, lights_status: LightsStatus | None = None) -> None:
        self.up_pin = Pin(button_up_pin, Pin.IN)
        self.down_pin = Pin(button_down_pin, Pin.IN)

        self.normal_press_duration = 100
        self.brightness_change_press_duration = 500
        self.on_off_state_change_multiplier = 10

        self.up_pin.irq(self._handle_up_irq, Pin.IRQ_FALLING | Pin.IRQ_RISING)
        self.down_pin.irq(self._handle_down_irq, Pin.IRQ_FALLING | Pin.IRQ_RISING)

        self._last_up_press = 0
        self._last_down_press = 0

        self._already_pressed_once = False

        if not lights_status:
            self.lights_status = LightsStatus(0, range(0, 999), 0, range(0, 999)) # Set an "infinitely" big celling for the range so it can be calibrated
            self.calibrate()
        else:
            self.lights_status = lights_status
            self.calibrate(False, False)

    def _handle_up_irq(self, pin):
        if pin.value() == 0:
            self._handle_up_press()
        else:
            self._handle_up_release()

    def _handle_down_irq(self, pin):
        if pin.value() == 0:
            self._handle_down_press()
        else:
            self._handle_down_release()

    def _handle_up_press(self) -> None:
        self._last_up_press = time.ticks_ms()

    def _handle_down_press(self) -> None:
        self._last_down_press = time.ticks_ms()

    def _handle_up_release(self) -> None:
        diff = time.ticks_diff(time.ticks_ms(), self._last_up_press)

        if diff >= self.brightness_change_press_duration:
            # Long press
            self.lights_status.change_brightness(int(diff / self.brightness_change_press_duration))
            return

        if self._already_pressed_once:
            self._already_pressed_once = False
            # Double press
            self.lights_status.change_color(1)
            return

        self._already_pressed_once = True

        def try_single_press():
            if self._already_pressed_once:
                self._already_pressed_once = False
                # Single press
                self.lights_status.on = True

        Timer().init(mode=Timer.ONE_SHOT, period=self.normal_press_duration * self.on_off_state_change_multiplier, callback=try_single_press)

    def _handle_down_release(self) -> None:
        diff = time.ticks_diff(time.ticks_ms(), self._last_down_press)

        if diff >= self.brightness_change_press_duration:
            # Long press
            self.lights_status.change_brightness(-int(diff / self.brightness_change_press_duration))
            return

        if self._already_pressed_once:
            self._already_pressed_once = False
            # Double press
            self.lights_status.change_color(-1)
            return

        self._already_pressed_once = True

        def try_single_press():
            if self._already_pressed_once:
                self._already_pressed_once = False
                # Single press
                self.lights_status.on = False

        Timer().init(mode=Timer.ONE_SHOT, period=self.normal_press_duration * self.on_off_state_change_multiplier, callback=try_single_press)

    def calibrate(self, do_set_brightness_range: bool = True, do_set_color_range: bool = True) -> LightsStatus:
        return self.lights_status

        i = 1
        def next_step(i):
            print(f"\033[0;36m={i}===============================================\033[0m")
            return i + 1

        def pause():
            input("\033[0;90mPress enter to continue...\033[0m")

        print("\033[1m[Follow the instructions start the calibration]\033[0m")
        i = next_step(i)
        print("Please turn the lights on, then set them to the lowest brightness setting and the warmest color setting (the light should be yellow / orange).")
        pause()

        self.lights_status.brightness_level = 0
        self.lights_status.color_level = 0

        if do_set_brightness_range:
            i = next_step(i)
            print("\033[1m[Calibrating brightness range]\033[0m")
            print("Please change the brightness until your desired minimum brightness is reached.")
            pause()

            brightness_range_bottom = self.lights_status.brightness_level

            print("Please change the brigtness until your desired maximum brightness is reached.")
            pause()

            brightness_range_top = self.lights_status.brightness_level

            if brightness_range_bottom > brightness_range_top:
                print("\033[0;33mWarning: You have set your maximum brigtness bellow your minimum brightness, swapping max and min.\033[0m")
                brightness_range_top, brightness_range_bottom = brightness_range_bottom, brightness_range_top

            self.lights_status.brightness_range = range(brightness_range_bottom, brightness_range_top)

            print("\033[0;32mSuccessfully calibrated brigtness range, setting brightness to the new minimum.\033[0m")

            for i in range(self.lights_status.brightness_range[-1] - self.lights_status.brightness_range[0]):
                self.brightness_down()

        if do_set_color_range:
            i = next_step(i)
            print("\033[1m[Calibrating warmth range]\033[0m")
            print("Please change the warmth until your desired warmest color is reached.")
            pause()

            color_range_bottom = self.lights_status.color_level

            print("Please change the warmth until your desired coldest color is reached.")
            pause()

            color_range_top = self.lights_status.color_level

            if color_range_bottom > color_range_top:
                print("\033[0;33mWarning: You have set your maximum warmth bellow your minimum warmth, swapping max and min.\033[0m")
                color_range_top, color_range_bottom = color_range_bottom, color_range_top

            self.lights_status.color_range = range(color_range_bottom, color_range_top)

            print("\033[0;32mSuccessfully calibrated warmth range, setting warmth to the new minimum.\033[0m")

            for i in range(self.lights_status.color_range[-1] - self.lights_status.color_range[0]):
                self.warmth_down()

        return self.lights_status

    def on(self) -> None:
        gpio_send_press(self.up_pin, self.normal_press_duration)
        time.sleep_ms(self.normal_press_duration * (self.on_off_state_change_multiplier - 1))

    def off(self) -> None:
        gpio_send_press(self.down_pin, self.normal_press_duration)
        time.sleep_ms(self.normal_press_duration * (self.on_off_state_change_multiplier - 1))

    def brightness_up(self) -> None:
        gpio_send_press(self.up_pin, self.brightness_change_press_duration)

    def brightness_down(self) -> None:
        gpio_send_press(self.down_pin, self.brightness_change_press_duration)

    def warmth_up(self) -> None:
        gpio_send_press(self.up_pin, self.normal_press_duration)
        gpio_send_press(self.up_pin, self.normal_press_duration)

    def warmth_down(self) -> None:
        gpio_send_press(self.down_pin, self.normal_press_duration)
        gpio_send_press(self.down_pin, self.normal_press_duration)
