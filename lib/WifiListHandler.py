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
		for byteLine in check_output("iwlist wlan0 scan | grep -e ESSID -e Encryption -e Quality", shell=True).splitlines():
			line = byteLine.decode("utf-8")
			if line.find('ESSID')>=0:
				if ssid:
					self.addNetwork(wifiList, ssid, network)
				network = {'encryption':False,'quality':'','signalLevel':''}
				ssid = line.split(':')[1].replace("\"","")
			elif line.find('Encryption key:on')>=0:
				network['encryption'] = True
			else:
				m = re.match('.*Quality=(\\d*)/100  Signal level=(\\d*)/100.*', line, re.M | re.I)
				if m:
					network['quality'] = m.group(1)
					network['signalLevel'] = m.group(2)

		if ssid:
			self.addNetwork(wifiList, ssid, network)

		wifiList = OrderedDict(sorted(wifiList.items(), key=lambda x: x[1]['quality']))
		wifiList = OrderedDict(reversed(list(wifiList.items())))
		self.write(wifiList)

	def addNetwork(self, wifiList, ssid, network):
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
