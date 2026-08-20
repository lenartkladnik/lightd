from controllers import BilresaController, LightsStatus
from web import Web, WifiConfig
from weather import get_weather
import uasyncio

with open(".config", "r") as f:
    config = dict([i.split("=") for i in f.read().splitlines()])

config_get_range = lambda name: range(int(config.get(name, '0,0').split(',')[0]), int(config.get(name, '0,0').split(',')[1]))

my_lights = LightsStatus(0, config_get_range('brightness_range'), 0, config_get_range('color_range'))
bilresa = BilresaController(int(config.get('gpio_up', -1)), int(config.get('gpio_down', -1)), my_lights)
wifi_conf = WifiConfig(config.get('ssid', ''), config.get('password', ''))
app = Web(wifi_conf)

bilresa.brightness_down(20) # Ensure brightness is 0
bilresa.lights_status.brightness_level = 0
print("Please set the warmth to the warmest tone.") # Assuming warmth is the warmest

async def update_lights():
    w = get_weather()

    target_brightness_level = bilresa.lights_status.brightness_range[0] + abs(bilresa.lights_status.brightness_range[0] - bilresa.lights_status.brightness_range[-1]) * w.darkness
    if w.is_rain and target_brightness_level < 0.8:
        target_brightness_level = 0.8

    dist = round(target_brightness_level - bilresa.lights_status.brightness_level)

    bilresa.change_brightness(dist)

    if target_brightness_level > 0.9 and bilresa.lights_status.color_level != 0:
        bilresa.change_warmth(-bilresa.lights_status.color_level)

    elif bilresa.lights_status.color_level == 0:
        bilresa.change_warmth(1)

    await uasyncio.sleep(300)

@app.route('/status')
def status():
    return str(bilresa.lights_status), 200, 'text/json'

@app.route('/on')
def on():
    bilresa.on()
    return 'Ok', 200, 'text/json'

@app.route('/off')
def off():
    bilresa.off()
    return 'Ok', 200, 'text/json'

@app.route('/brightness-up')
def brightness_up():
    bilresa.brightness_up()
    return 'Ok', 200, 'text/json'

@app.route('/brightness-down')
def brightness_down():
    bilresa.brightness_down()
    return 'Ok', 200, 'text/json'

@app.route('/color-up')
def color_up():
    bilresa.warmth_up()
    return 'Ok', 200, 'text/json'

@app.route('/color-down')
def color_down():
    bilresa.warmth_down()
    return 'Ok', 200, 'text/json'

async def main():
    uasyncio.create_task(app.serve('0.0.0.0', 80))
    uasyncio.create_task(update_lights())

    while True:
        await uasyncio.sleep(1)

uasyncio.run(main())
