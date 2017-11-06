# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# WIFI List Handler
#
# Copyright (C) 2017 Markus Heidt <markus@heidt-tech.com>
#
#********************************************************************
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For a full copy of the GNU General Public License see the LICENSE.txt file.
#
#********************************************************************

import os
import re
import logging
import tornado.web
from subprocess import check_output
from collections import OrderedDict

#------------------------------------------------------------------------------
# Wifi List Handler
#------------------------------------------------------------------------------
class WifiListHandler(tornado.web.RequestHandler):

	def get_current_user(self):
		return self.get_secure_cookie("user")

	@tornado.web.authenticated
	def get(self):
		wifiList = OrderedDict()
		try:
			network = None
			ssid = None
			encryption = False
			quality = 0
			signalLevel = 0

			for byteLine in check_output("iwlist wlan0 scan | grep -e ESSID -e Encryption -e Quality", shell=True).splitlines():
				line = byteLine.decode("utf-8")
				if line.find('ESSID')>=0:
					network = {'encryption':False, 'quality':0, 'signalLevel':0}
					ssid = line.split(':')[1].replace("\"","")
					if ssid:
							self.add_network(wifiList, ssid, network, encryption, quality, signalLevel)
							logging.info("Found Network: %s" % ssid)
					encryption = False
					quality = 0
					signalLevel = 0
				elif line.find('Encryption key:on')>=0:
					encryption = True
				else:
					m = re.match('.*Quality=(.*?)/(.*?) Signal level=(.*?(100|dBm)).*', line, re.M | re.I)
					if m:
						quality = round(int(m.group(1)) / int(m.group(2)) * 100,2)
						signalLevel = m.group(3)

			wifiList = OrderedDict(sorted(wifiList.items(), key=lambda x: x[1]['quality']))
			wifiList = OrderedDict(reversed(list(wifiList.items())))

		except:
			pass
		self.write(wifiList)


	def add_network(self, wifiList, ssid, network, encryption, quality, signalLevel):
		network['quality'] = quality
		network['signalLevel'] = signalLevel
		network['encryption'] = encryption
		if ssid in wifiList:
			existingNetwork = wifiList[ssid]
			if existingNetwork:
				if existingNetwork['quality'] < network['quality']:
					existingNetwork['quality'] = network['quality']
					existingNetwork['signalLevel'] = network['signalLevel']
			else:
				wifiList.update({ssid:network})
		else:
			wifiList.update({ssid:network})
