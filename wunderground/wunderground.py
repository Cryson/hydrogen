import os
import json
import urllib2
import ConfigParser
import logging
import time

logging.basicConfig(filename='log/hydrogen.log', level=logging.INFO)

Config = ConfigParser.ConfigParser()
Config.read('wunderground/config/config.ini')

user_apiid = Config.get('weather_settings', 'user_apiid')
user_city = Config.get('weather_settings', 'user_city')
user_state = Config.get('weather_settings', 'user_state')


def getWeatherCondition():
	try:
		url = "http://api.wunderground.com/api/"
		url += "%s/conditions/q/%s/" % (user_apiid, user_state)
		url += "%s.json" % user_city
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		jsondata = response.read()
		return jsondata
	except Exception as e:
		print("Could not get weather data")
		return e

def checkcache_mtime():
	epoch = os.path.getmtime('wunderground/cache/wunderground.cache')
	currenttime = time.time()
	seconds = currenttime - epoch
	minutes = seconds // 60 % 60

	return minutes

def pull_weather_json():
	weather = getWeatherCondition()
	w = json.loads(weather)

	# Grab Weather Data
	currenttemp = float(w['current_observation']['temp_f'])
	atmospressure = float(w['current_observation']['pressure_in'])
	windspeed = float(w['current_observation']['wind_mph'])
	humidity = w['current_observation']['relative_humidity']
	humidity = humidity[:-1]
	humidity = float(humidity)
	feels_like = float(w['current_observation']['feelslike_f'])
	dewpoint = float(w['current_observation']['dewpoint_f'])

	with open('wunderground/cache/wunderground.cache', 'w') as data_file:
		data_file.write('%s' % currenttemp)	

	return currenttemp


def get_current_temperature():
	minutes = checkcache_mtime()
	if minutes > 30:
		logging.info("Pulling new outside temperature")
		temp = pull_weather_json()
		return temp
	elif minutes < 30:
		logging.info("Using cached outside temperature, as old temp isn't 30 minutes old")
		with open('wunderground/cache/wunderground.cache', 'r') as data_file:
			temp = data_file.read()
			return temp 



