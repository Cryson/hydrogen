#!/usr/bin/env python

import sys
import os
import logging
import requests
import datetime
import subprocess
import json

from ecobee import ecobee
from hydrogen import hydrogen
from wunderground import wunderground

logging.basicConfig(filename='log/hydrogen.log', level=logging.INFO)

# Set your ecobee index list
thermostatlist = [0, 1]


def internet_check():
	with open(os.devnull, 'w') as DEVNULL:
		try:
			subprocess.check_call(
				['ping', '-c', '3', '8.8.8.8'],
				stdout=DEVNULL,  # suppress output
				stderr=DEVNULL
			)
			is_up = 0
		except subprocess.CalledProcessError:
			is_up = 1
	return is_up


def main():
	now = datetime.datetime.now()
	logging.info("######################")
	logging.info("Hydrogen ran at " + str(now))
	logging.info("######################")

	ping_check = internet_check()
	if ping_check != 0:
		logging.error("Internet is down, exiting!")
		sys.exit(1)
	elif ping_check == 0:
		logging.info("Internet is up! Continuing")

	""" Check for occupancy and act accordingly """
        with open('ecobee/data/ecobee_tokens.json') as data_file:
                data = json.load(data_file)
                refresh_token = data['refresh_token']

	ecobee.refresh_tokens(refresh_token)
	program = ecobee.get_current_climate_setting(1)
	occupancy = ecobee.get_remote_sensors(0)[1]['capability'][2]['value']  # Check if someone is home via proximity
	peakhours = hydrogen.hydrogen()
	if peakhours == 1:
		logging.info("Peak hours WERE found in hydrogen_check_gmail")
		result = 1
	elif peakhours != 1:
		logging.info("Peak hours were not found in Hydrogen")
		if program == "sleep":
			logging.info("Ecobee is reporting sleep program, setting result to 2")
			result = 2
		elif program != "sleep":
			if occupancy == "true":
				with open('hydrogen/cache/occupancy.cache', 'w') as outfile:
					outfile.write("0")
				logging.info("Someone is home, setting result to 2")
				result = 2
			elif occupancy == "false":
				with open('hydrogen/cache/occupancy.cache', 'r') as infile:
					occupancyint = int(infile.read())
				with open('hydrogen/cache/occupancy.cache', 'w') as outfile:
					occupancyint += 1
					outfile.write(str(occupancyint))
					logging.info("Occupancy said nobody is home, increasing cache to " + str(occupancyint))
				with open('hydrogen/cache/occupancy.cache', 'r') as infile:
					occupancyint = int(infile.read())
				if occupancyint >= 18:
					logging.info("Looks like nobody is home, turning to off hvac mode to save power")
					result = 4
				elif occupancyint <= 17:
					logging.info("Occupancy is less than 17, result is being set to 2")
					result = 2

	""" Check for results of test and act accordingly """
	""" Result of 1 means that the ecobees need to be turned off to avoid peak hours """
	if result == 1:  # Peak hours!
		logging.info("Gmail check has come back with peak hours, setting ecobees to off hvac mode")
		for i in thermostatlist:
			requesthvacset = ecobee.set_hvac_mode(i, 'off')
			if requesthvacset.status_code == requests.codes.ok:
				logging.info("Successfully set thermostat index " + str(i) + " to off hvac mode")
	elif result == 2:  # Someone is home or asleep, and/or not peak hours
		ctemp = wunderground.get_current_temperature()
		logging.info("Result was 2, current outside temperature returned " + str(ctemp) + " degrees F")
		if ctemp >= 51:
			hvacmode = 'cool'
		elif ctemp <= 50:
			hvacmode = 'heat'

		for i in thermostatlist:
			requesthvacset = ecobee.set_hvac_mode(i, hvacmode)
			if requesthvacset.status_code == requests.codes.ok:
				logging.info("Successfully set thermostat index " + str(i) + " to " + hvacmode + " hvac mode")
	elif result == 4:  # Nobody is home
		for i in thermostatlist:
			requesthvacset = ecobee.set_hvac_mode(i, 'off')
			if requesthvacset.status_code == requests.codes.ok:
				logging.info("Successfully set thermostat index " + str(i) + " to off hvac mode")
	elif result == 0:  # Not peak hours
		logging.info("No Peak Hours have been set by CobbEMC, we're good!")
		sys.exit(0)

if __name__ == '__main__':
	os.path.dirname(os.path.realpath(__file__))
	main()
