import json
import requests
import sys

with open('data/ecobee_secret.json') as data_file:
	data = json.load(data_file)
	apikey = data['apikey']


# Only used to initialize the ecobee application on the developer console (myapp) console on ecobee.com
def get_ecobee_pin():
	try:
		url = "https://api.ecobee.com/authorize"
		params = {'response_type': 'ecobeePin', 'client_id': apikey, 'scope': 'smartWrite'}
		request = requests.get(url, params=params)
		with open('data/ecobee_authentication.json', 'w') as outfile:
			json.dump(request.json(), outfile)
	except Exception as e:
		print(e)
		sys.exit(1)

get_ecobee_pin()
