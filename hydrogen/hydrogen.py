from __future__ import print_function
import httplib2
import os
import logging
import datetime

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


def check_gmail():
	valid=''
	credentials = get_credentials()
	http = credentials.authorize(httplib2.Http())
	service = discovery.build('gmail', 'v1', http=http)
	today = str(datetime.date.today())
	yesterday = str(datetime.date.fromordinal(datetime.date.today().toordinal() - 1))
	todayhours = int(datetime.datetime.now().strftime("%H"))  # Hour of the day in 24 hour format

	if todayhours not in range(14, 19):  # Check if it is peak hours for CobbEMC
		return 2

	# Check Gmail messages with label 41(CobbEMC Peak Hours)
	messages = service.users().messages().list(userId='me', labelIds='Label_41').execute().get('messages', [])
	for message in messages:
		tdata = service.users().messages().get(userId='me', id=message['id']).execute()
		epochtime = str(tdata['internalDate'])
		emaildate = str(datetime.datetime.fromtimestamp(float(epochtime.replace(' ', '')[:-3].upper())).strftime("%Y-%m-%d"))
		if emaildate == yesterday:
			valid = 1
			break

	if valid == 1:
		logging.info("Ecobee's need to be turned off to avoid peak hours that CobbEMC has set for " + today + " from 2 P.M. EST to 7 P.M. EST")
		return 1
	else:
		return 0


