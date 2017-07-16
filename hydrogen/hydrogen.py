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
	minutes = seconds // 60 % 60
	return minutes


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
			data_file.write(emaildate)


def hydrogen():
	valid=''
	minutes = checkcache_mtime()
	yesterday = str(datetime.date.fromordinal(datetime.date.today().toordinal() - 1))
	todayhours = int(datetime.datetime.now().strftime("%H"))  # Hour of the day in 24 hour format

	if todayhours not in range(14, 19):  # Check if it is peak hours for CobbEMC
		return 2

	if minutes < 288:
		logging.info("Messages cache file is not 288 minutes old, reading from cache file")
		with open('hydrogen/cache/messages.cache') as data_file:
			for line in data_file:
				if line == yesterday:
					valid = 1
					break
	elif minutes > 288:
		open('hydrogen/cache/messages.cache', 'w').close()  # Clear the cache file
		check_gmail()
		with open('hydrogen/cache/messages.cache') as data_file:
			for line in data_file:
				if line == yesterday:
					valid = 1
					break

	if valid == 1:
		logging.info("Ecobee's need to be turned off to avoid peak hours that CobbEMC has set for " + today + " from 2 P.M. EST to 7 P.M. EST")
		return 1
	elif:
		logging.error("Something went wrong with the hydrogen message cache and we couldn't read the dates")
		return 2
