import requests
import gc
import ujson
import utime
from math import cos, pi

class WeatherData:
    def __init__(self, darkness: float, is_rain: bool) -> None:
        self.darkness = darkness
        self.is_rain = is_rain

def _iso_to_epoch(s):
    date_part, time_part = s.split("T")
    year, month, day = map(int, date_part.split("-"))

    if "+" in time_part:
        time_str, _, offset = time_part.partition("+")
        tz_sign = 1
    elif time_part.count("-") > 0:
        time_str, _, offset = time_part.partition("-")
        tz_sign = -1
    else:
        time_str, offset = time_part, "00:00"
        tz_sign = 1

    hour, minute, second = map(int, time_str.split(":"))
    off_h, off_m = map(int, offset.split(":"))
    tz_offset_seconds = tz_sign * (off_h * 3600 + off_m * 60)

    t = (year, month, day, hour, minute, second, 0, 0)
    epoch_local = utime.mktime(t)
    epoch_utc = epoch_local - tz_offset_seconds
    return epoch_utc

def _get_weather_arso(url) -> WeatherData:
    weather_data = WeatherData(False, False)

    gc.collect()
    resp = requests.get(url)
    text = resp.text
    resp.close()
    gc.collect()

    start = text.find('"observation"')
    start = text.find('{', start)
    text = text[start:]
    gc.collect()
    depth = 0
    end = start
    for i in range(len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    obs_text = text[:end]
    del text
    gc.collect()

    obs = ujson.loads(obs_text)

    today = obs['features'][0]['properties']['days'][0]

    del obs
    gc.collect()

    sunrise = _iso_to_epoch(today['sunrise'])
    sunset = _iso_to_epoch(today['sunset'])
    now = utime.mktime(utime.gmtime())

    mid_day = (sunset + sunrise) / 2
    half_day = (sunset - sunrise) / 2

    weather_data.darkness = max(0, min(1, (1 + cos(pi * (now - mid_day) / half_day)) / 2))

    del sunrise
    del sunset
    del mid_day

    today = today['timeline'][0]

    gc.collect()

    if "dež" in today['clouds_shortText']:
        weather_data.is_rain = True

    return weather_data

def get_weather() -> WeatherData:
    url = "https://vreme.arso.gov.si/api/1.0/location/?lang=sl&location=Ljubljana"
    return _get_weather_arso(url)
