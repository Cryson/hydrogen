import json
import requests
import logging
import sys
import time

logging.basicConfig(filename='log/hydrogen.log', level=logging.INFO)

with open('ecobee/data/ecobee_secret.json') as data_file:
	data = json.load(data_file)
	apikey = data['apikey']

with open('ecobee/data/ecobee_authentication.json') as data_file:
	data = json.load(data_file)
	authcode = data['code']


# Get initial tokens
def get_tokens():
	url = 'https://api.ecobee.com/token'
	params = {'grant_type': 'ecobeePin', 'code': authcode, 'client_id': apikey}
	request = requests.post(url, params=params)
	if request.status_code == requests.codes.ok:
		with open('ecobee/data/ecobee_tokens.json', 'w') as outfile:
			json.dump(request.json(), outfile)
	else:
		print('Error while requesting tokens from ecobee.com.' + ' Status code: ' + str(request.status_code))


# Refresh bad tokens
def refresh_tokens(refresh_token):
	url = 'https://api.ecobee.com/token'
	params = {'grant_type': 'refresh_token',
				'refresh_token': refresh_token,
				'client_id': apikey}
	request = requests.post(url, params=params)
	if request.status_code == requests.codes.ok:
		with open('ecobee/data/ecobee_tokens.json', 'w') as outfile:
			json.dump(request.json(), outfile)
	else:
		sys.exit(4)


# Get all data for all thermostats
def get_thermostats(attempts=0):
	with open('ecobee/data/ecobee_tokens.json') as data_file:
		data = json.load(data_file)
		accesstoken = data['access_token']
		refresh_token = data['refresh_token']

	url = 'https://api.ecobee.com/1/thermostat'
	header = {'Content-Type': 'application/json;charset=UTF-8', 'Authorization': 'Bearer ' + accesstoken}
	params = {'json': ('{"selection":{"selectionType":"registered",'
						'"includeRuntime":"true",'
						'"includeSensors":"true",'
						'"includeProgram":"true",'
						'"includeEquipmentStatus":"true",'
						'"includeWeather":"true",'
						'"includeEvents":"true",'
						'"includeSettings":"true"}}')}
	request = requests.get(url, headers=header, params=params)
	if 'thermostatList' not in request.json():
		if attempts <= 3:
			attempts += 1
			logging.info("thermostatList not found in ecobee json payload. BAD! Trying again, this is the " + str(attempts) + " attempt")
			time.sleep(15)
			refresh_tokens(refresh_token)
			get_thermostats(attempts)
		elif attempts > 3:
			logging.info("ecobee payload failed. attempts were greater than 3, trying again later")
			sys.exit(0)
	
	if request.status_code == requests.codes.ok:
		thermostats = request.json()['thermostatList']
		return thermostats
	else:
		if refresh_tokens(refresh_token):
			return get_thermostats()
		else:
			return None


# Set your HVAC Mode
def set_hvac_mode(index, hvac_mode):
	""" possible hvac modes are auto, auxHeatOnly, cool, heat, off
	indexes for thermostats are 0 (downstairs) and 1 (upstairs) """
	with open('ecobee/data/ecobee_tokens.json') as data_file:
		data = json.load(data_file)
		accesstoken = data['access_token']
	thermostats = get_thermostats()
	url = 'https://api.ecobee.com/1/thermostat'
	header = {'Content-Type': 'application/json;charset=UTF-8', 'Authorization': 'Bearer ' + accesstoken}
	params = {'format': 'json'}
	body = ('{"selection":{"selectionType":"thermostats","selectionMatch":'
			'"' + thermostats[index]['identifier'] +
			'"},"thermostat":{"settings":{"hvacMode":"' + hvac_mode +
			'"}}}')
	request = requests.post(url, headers=header, params=params, data=body)
	if request.status_code == requests.codes.ok:
		logging.info("Setting Ecobee to " + hvac_mode + " hvac mode on Ecobee index " + str(index))
		return request
	else:
		logger.warn("Error connecting to Ecobee while attempting to set HVAC mode.  Refreshing tokens...")
		refresh_tokens()


def get_remote_sensors(index):
	''' Return remote sensors based on index '''
	thermostats = get_thermostats()
	return thermostats[index]['remoteSensors']


def get_current_climate_setting(index):
	''' Return sleep, away, or home '''
	thermostats = get_thermostats()
	return thermostats[index]['program']['currentClimateRef']
