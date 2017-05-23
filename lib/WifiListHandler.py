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
		network = None
		ssid = None
		encryption = False
		quality = 0
		signalLevel = 0
		for byteLine in check_output("iwlist wlan0 scan | grep -e ESSID -e Encryption -e Quality", shell=True).splitlines():
			line = byteLine.decode("utf-8")
			if line.find('ESSID')>=0:
				if ssid:
						self.addNetwork(wifiList, ssid, network, encryption, quality, signalLevel)
				network = {'encryption':False,'quality':0,'signalLevel':0}
				encryption = False
				quality = 0
				signalLevel = 0
				ssid = line.split(':')[1].replace("\"","")
			elif line.find('Encryption key:on')>=0:
				encryption = True
			else:
				m = re.match('.*Quality=(.*?)/(.*?) Signal level=(.*?(100|dBm)).*', line, re.M | re.I)
				if m:
					quality = round(int(m.group(1)) / int(m.group(2)) * 100,2)
					signalLevel = m.group(3)

		if ssid:
			self.addNetwork(wifiList, ssid, network, encryption, quality, signalLevel)

		wifiList = OrderedDict(sorted(wifiList.items(), key=lambda x: x[1]['quality']))
		wifiList = OrderedDict(reversed(list(wifiList.items())))
		self.write(wifiList)


	def addNetwork(self, wifiList, ssid, network, encryption, quality, signalLevel):
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
