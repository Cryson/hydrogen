#!/usr/bin/env python

import sys
import os
import logging
import requests
import datetime

from ecobee import ecobee
from hydrogen import hydrogen
from wunderground import wunderground

logging.basicConfig(filename='log/hydrogen.log', level=logging.DEBUG)

# Set your ecobee index list
thermostatlist = [0, 1]


def main():
	now = datetime.datetime.now()
	logging.info("Hydrogen ran at " + str(now))

	""" Check for occupancy and act accordingly """
	program = ecobee.get_current_climate_setting(1)
	occupancy = ecobee.get_remote_sensors(0)[1]['capability'][2]['value']  # Check if someone is home via proximity
	if program == "sleep":
		logging.info("Ecobee is reporting sleep program, setting result to 2")
		result = 2
	elif program != "sleep":
		occupancy = ecobee.get_remote_sensors(0)[1]['capability'][2]['value']  # Check if someone is home via proximity
		if occupancy == "true":
			with open('hydrogen/cache/occupancy.cache', 'w') as outfile:
				outfile.write("0")
			logging.info("Someone is home, setting result to 2")
			result = 2
		elif occupancy == "false":
			with open('hydrogen/cache/occupancy.cache', 'r') as infile:
				occupancyint = infile.read()
			with open('hydrogen/cache/occupancy.cache', 'w') as outfile:
				occupancyint += 1
				outfile.write(occupancyint)
				logging.info("Occupancy said nobody is home, increasing cache to " + str(occupancyint))
			with open('hydrogen/cache/occupancy.cache', 'r') as infile:
				occupancyint = infile.read()
			if occupancyint >= 9:
				logging.info("Looks like nobody is home, turning to off hvac mode to save power")
				result = 4
			elif occupancyint <= 8:
				result = hydrogen.check_gmail()

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
		if ctemp >= 66:
			hvacmode = 'cool'
		elif ctemp <= 65:
			hvacmode = 'heat'

		if occupancy == "false":
			logging.info("It's not peak hours right now, setting ecobees to " + hvacmode)

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
