import sys
import logging
import requests
import datetime


from ecobee import ecobee
from hydrogen import hydrogen

logging.basicConfig(filename='log/hydrogen.log', level=logging.DEBUG)
now = datetime.datetime.now()
logging.info("Hydrogen ran at " + str(now))

# Set your ecobee index list
thermostatlist = [0, 1]


def main():
	""" Result of 1 means that the ecobees need to be turned off to avoid peak hours """
	result = hydrogen.check_gmail()
	if result == 1:
		logging.info("Gmail check has come back with peak hours, setting ecobees to off hvac mode")
		for i in thermostatlist:
			requesthvacset = ecobee.set_hvac_mode(i, 'off')
			if requesthvacset.status_code == requests.codes.ok:
				logging.info("Successfully set thermostat index " + str(i) + " to off hvac mode")
	elif result == 2:
		logging.info("It's not peak hours right now, setting ecobees to cool")
		for i in thermostatlist:
			requesthvacset = ecobee.set_hvac_mode(i, 'cool')
			if requesthvacset.status_code == requests.codes.ok:
				logging.info("Successfully set thermostat index " + str(i) + " to cool hvac mode")
	elif result == 0:
		logging.info("No Peak Hours have been set by CobbEMC, we're good!")
		sys.exit(0)

if __name__ == '__main__':
	main()
