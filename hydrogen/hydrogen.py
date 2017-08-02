from __future__ import print_function
import httplib2
import os
import logging
import datetime
import time

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
	import argparse
	flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
	flags = None

logging.basicConfig(filename='log/hydrogen.log', level=logging.DEBUG)

SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'hydrogen/data/client_secret.json'
APPLICATION_NAME = 'Hydrogen'


def get_credentials():
	home_dir = os.path.expanduser('~')
	credential_dir = os.path.join(home_dir, '.credentials')
	if not os.path.exists(credential_dir):
		os.makedirs(credential_dir)
	credential_path = os.path.join(credential_dir, 'gmail-python-quickstart.json')

	store = Storage(credential_path)
	credentials = store.get()
	if not credentials or credentials.invalid:
		flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
		flow.user_agent = APPLICATION_NAME
		if flags:
			credentials = tools.run_flow(flow, store, flags)
		else:  # Needed only for compatibility with Python 2.6
			credentials = tools.run(flow, store)
		logging.info('Storing credentials to ' + credential_path)
	return credentials


def checkcache_mtime():
	epoch = os.path.getmtime('hydrogen/cache/messages.cache')
	currenttime = time.time()
	seconds = currenttime - epoch
	hours = seconds // 3600 % 24
	return hours 


def check_gmail():
	credentials = get_credentials()
	http = credentials.authorize(httplib2.Http())
	service = discovery.build('gmail', 'v1', http=http, cache_discovery=False)

	# Check Gmail messages with label 41(CobbEMC Peak Hours)
	messages = service.users().messages().list(userId='me', labelIds='Label_41').execute().get('messages', [])
	for message in messages:
		tdata = service.users().messages().get(userId='me', id=message['id']).execute()
		epochtime = str(tdata['internalDate'])
		emaildate = str(datetime.datetime.fromtimestamp(float(epochtime.replace(' ', '')[:-3].upper())).strftime("%Y-%m-%d"))
		with open('hydrogen/cache/messages.cache', 'a') as data_file:
			data_file.write(emaildate + "\n")


def hydrogen():
	valid=''
	cache_age = checkcache_mtime()
	yesterday = str(datetime.date.fromordinal(datetime.date.today().toordinal() - 1))
	todayhours = int(datetime.datetime.now().strftime("%H"))  # Hour of the day in 24 hour format
	today = str(datetime.date.today())

	if todayhours not in range(14, 19):  # Check if it is peak hours for CobbEMC
		logging.info("Hydrogen is reporting that it's not peak hours. Current hour is " + str(todayhours))
		return 2

	if cache_age <= 4:
		logging.info("Messages cache file is not 5 hours old, reading from cache file")
		with open('hydrogen/cache/messages.cache') as data_file:
			for line in data_file:
				if line.rstrip('\n') == yesterday:
					valid = 1
					break
	elif cache_age >= 5:
		logging.info("Messages cache file is 5 hours old, grabbing new gmail data")
		open('hydrogen/cache/messages.cache', 'w').close()  # Clear the cache file
		check_gmail()
		with open('hydrogen/cache/messages.cache') as data_file:
			for line in data_file:
				if line.rstrip('\n') == yesterday:
					valid = 1
					break

	if valid == 1:
		logging.info("Ecobee's need to be turned off to avoid peak hours that CobbEMC has set for " + today + " from 2 P.M. EST to 7 P.M. EST")
		return 1
	elif valid != 1:
		logging.info("No dates in the Hydrogen messages cache match yesterdays date! No Peak Hours!")
		return 2
