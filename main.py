from controllers import BilresaController, LightsStatus
from web import Web, WifiConfig

with open(".config", "r") as f:
    config = dict([i.split("=") for i in f.read().splitlines()])

config_get_range = lambda name: range(int(config.get(name, '0,0').split(',')[0]), int(config.get(name, '0,0').split(',')[1]))

my_lights = LightsStatus(0, config_get_range('brightness_range'), 0, config_get_range('color_range'))
bilresa = BilresaController(int(config.get('gpio_up', -1)), int(config.get('gpio_down', -1)), my_lights)
wifi_conf = WifiConfig(config.get('ssid', ''), config.get('password', ''))
app = Web(wifi_conf)

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

app.serve('0.0.0.0', 80)
