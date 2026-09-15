from machine import Pin, Timer
import time
from log import log

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

    def __repr__(self) -> str:
        repr = f"brightness_level={self.brightness_level},\nbrightness_range={self.brightness_range},\ncolor_level={self.color_level},\ncolor_range={self.color_range},\non={self.on}"

        log(f"Requested lights status is:\n{repr}\n")

        return repr

    def change_brightness(self, n: int):
        if self.on:
            self.brightness_level += n
            if self.brightness_level < 0:
                self.brightness_level = 0

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
        self.brightness_change_press_duration = 1100
        self.brightness_change_rate = 220
        self.on_off_state_change_multiplier = 10

        self.up_pin.irq(self._handle_up_irq, Pin.IRQ_FALLING | Pin.IRQ_RISING)
        self.down_pin.irq(self._handle_down_irq, Pin.IRQ_FALLING | Pin.IRQ_RISING)

        self._last_up_press = 0
        self._last_down_press = 0

        self._already_pressed_once = False

        if lights_status:
            self.lights_status = lights_status

        else:
            self.lights_status = LightsStatus(0, range(0, 99), 0, range(0, 99)) # Has to be calibrated

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
        log("Pressed up.")

        self._last_up_press = time.ticks_ms()

    def _handle_down_press(self) -> None:
        log("Pressed down.")

        self._last_down_press = time.ticks_ms()

    def _handle_up_release(self) -> None:
        log("Released up.")

        diff = time.ticks_diff(time.ticks_ms(), self._last_up_press)

        if diff >= self.brightness_change_press_duration:
            # Long press
            self.lights_status.change_brightness(int((diff - self.brightness_change_press_duration) / self.brightness_change_rate))
            self._already_pressed_once = False
            return

        if self._already_pressed_once:
            self._already_pressed_once = False
            # Double press
            self.lights_status.change_color(1)
            return

        self._already_pressed_once = True

        def try_single_press(_):
            if self._already_pressed_once:
                self._already_pressed_once = False
                # Single press
                self.lights_status.on = True

        Timer().init(mode=Timer.ONE_SHOT, period=self.normal_press_duration * self.on_off_state_change_multiplier, callback=try_single_press)

    def _handle_down_release(self) -> None:
        log("Released down.")

        diff = time.ticks_diff(time.ticks_ms(), self._last_down_press)

        if diff >= self.brightness_change_press_duration:
            # Long press
            self.lights_status.change_brightness(-int((diff - self.brightness_change_press_duration) / self.brightness_change_rate))
            self._already_pressed_once = False
            return

        if self._already_pressed_once:
            self._already_pressed_once = False
            # Double press
            self.lights_status.change_color(-1)
            return

        self._already_pressed_once = True

        def try_single_press(_):
            if self._already_pressed_once:
                self._already_pressed_once = False
                # Single press
                self.lights_status.on = False

        Timer().init(mode=Timer.ONE_SHOT, period=self.normal_press_duration * self.on_off_state_change_multiplier, callback=try_single_press)

    def on(self) -> None:
        log("Turn lights on.")

        gpio_send_press(self.up_pin, self.normal_press_duration)
        time.sleep_ms(self.normal_press_duration * (self.on_off_state_change_multiplier - 1))

    def off(self) -> None:
        log("Turn lights off.")

        gpio_send_press(self.down_pin, self.normal_press_duration)
        time.sleep_ms(self.normal_press_duration * (self.on_off_state_change_multiplier - 1))

    def brightness_up(self, amount: float = 1) -> None:
        log("Turn brightness up.")

        gpio_send_press(self.up_pin, int(self.brightness_change_press_duration + self.brightness_change_rate * amount))

    def brightness_down(self, amount: float = 1) -> None:
        log("Turn brightness down.")

        gpio_send_press(self.down_pin, int(self.brightness_change_press_duration + self.brightness_change_rate * amount))

    def change_brightness(self, amount: float) -> None:
        log(f"Changing brightness by {amount}")

        if (amount < 0):
            self.brightness_down(abs(amount))
        else:
            self.brightness_up(amount)

    def warmth_up(self) -> None:
        log("Turn warmth up.")

        gpio_send_press(self.up_pin, self.normal_press_duration)
        gpio_send_press(self.up_pin, self.normal_press_duration)

    def warmth_down(self) -> None:
        log("Turn warmth down.")

        gpio_send_press(self.down_pin, self.normal_press_duration)
        gpio_send_press(self.down_pin, self.normal_press_duration)

    def change_warmth(self, amount: int) -> None:
        log(f"Changing warmth by {amount}")

        if (amount < 0):
            for _ in range(abs(amount)):
                self.warmth_down()

        else:
            for _ in range(amount):
                self.warmth_up()
