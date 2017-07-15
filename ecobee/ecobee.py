import json
import requests
import logging

logging.basicConfig(filename='log/hydrogen.log', level=logging.DEBUG)

with open('ecobee/data/ecobee_secret.json') as data_file:
	data = json.load(data_file)
	apikey = data['apikey']

with open('ecobee/data/ecobee_authentication.json') as data_file:
	data = json.load(data_file)
	authcode = data['code']


# Only used to initialize the ecobee application on the developer console (myapp) console on ecobee.com
def get_ecobee_pin():
	url = "https://api.ecobee.com/authorize"
	params = {'response_type': 'ecobeePin', 'client_id': apikey, 'scope': 'smartWrite'}
	request = requests.get(url, params=params)
	with open('ecobee/data/ecobee_authentication.json', 'w') as outfile:
		json.dump(request.json(), outfile)


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
def get_thermostats():
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
						'"includeEvents":"true",'
						'"includeSettings":"true"}}')}
	request = requests.get(url, headers=header, params=params)
	if request.status_code == requests.codes.ok:
		authenticated = True
		thermostats = request.json()['thermostatList']
		return thermostats
	else:
		authenticated = False
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


def get_weather(index):
	with open('ecobee/data/ecobee_tokens.json') as data_file:
		data = json.load(data_file)
		accesstoken = data['access_token']
	thermostats = get_thermostats()
	url = 'https://api.ecobee.com/1/thermostat'
	header = {'Content-Type': 'application/json;charset=UTF-8', 'Authorization': 'Bearer ' + accesstoken}
	params = {'format': 'json'}
	body = ('{"selection":{"selectionType":"thermostats","selectionMatch":'
			'"' + thermostats[index]['identifier'] +
			'"},"thermostat":{"weatherforecast":{"temperature":"}}}')
	request = requests.post(url, headers=header, params=params, data=body)
	print request.json()
