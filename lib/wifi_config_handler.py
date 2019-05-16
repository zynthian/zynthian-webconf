# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# WIFI Configuration Handler
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
import sys
import logging
import base64
import tornado.web
from os.path import isfile
from collections import OrderedDict
from subprocess import check_output

from lib.zynthian_config_handler import ZynthianBasicHandler

sys.path.append(os.environ.get('ZYNTHIAN_UI_DIR'))
import zynconf

#------------------------------------------------------------------------------
# Wifi Config Handler
#------------------------------------------------------------------------------

class WifiConfigHandler(ZynthianBasicHandler):

	wpa_supplicant_config_fpath = os.environ.get('ZYNTHIAN_CONFIG_DIR', "/zynthian/config") + "/wpa_supplicant.conf"
	passwordMask = "*****"
	fieldMap = { "ZYNTHIAN_WIFI_PRIORITY": "priority" }


	@tornado.web.authenticated
	def get(self, errors=None):
		supplicant_data = re.sub(r'psk=".*?"', 'psk="' + WifiConfigHandler.passwordMask + '"',
			self.read_supplicant_data(),
			re.I | re.M | re.S )
		p = re.compile('.*?network=\\{.*?ssid=\\"(.*?)\\".*?psk=\\"(.*?)\\".*?priority=(\d*).*?\\}.*?', re.I | re.M | re.S )
		iterator = p.finditer(supplicant_data)
		config=OrderedDict([
			['ZYNTHIAN_WIFI_WPA_SUPPLICANT', {
				'type': 'textarea',
				'cols': 50,
				'rows': 20,
				'title': 'Advanced Config',
				'value': supplicant_data
			}],
			['ZYNTHIAN_WIFI_MODE', {
				'type': 'select',
				'title': 'Mode',
				'value': zynconf.get_current_wifi_mode(),
				'options': ["off", "on", "hotspot"],
			}]
		])

		networks = []
		idx = 0
		for m in iterator:
			networks.append({
				'idx': idx,
				'ssid': m.group(1),
				'ssid64': base64.b64encode(m.group(1).encode())[:5],
				'psk': m.group(2),
				'priority': m.group(3)
			})
			idx+=1

		config['ZYNTHIAN_WIFI_NETWORKS'] = networks

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="wifi.html", config=config, title="Wifi", errors=errors)


	@tornado.web.authenticated
	def post(self):
		errors = []

		try:
			#Remove CR characters added by x-www-form-urlencoded
			wpa_supplicant_data = self.get_argument('ZYNTHIAN_WIFI_WPA_SUPPLICANT').replace("\r\n", "\n")

			#Apply changes: delete network, change password, ...
			wpa_supplicant_data = self.apply_updated_fields(wpa_supplicant_data, ["ZYNTHIAN_WIFI_PRIORITY"])

			newSSID = self.get_argument('ZYNTHIAN_WIFI_NEW_SSID')
			if newSSID:
				wpa_supplicant_data = self.add_new_network(wpa_supplicant_data, newSSID)

			fo = open(self.wpa_supplicant_config_fpath, "w")
			fo.write(wpa_supplicant_data)
			fo.flush()
			fo.close()

		except Exception as e:
			errors.append(e)

		try:
			wifi_mode = self.get_argument('ZYNTHIAN_WIFI_MODE')
			if wifi_mode == "on":
				if not zynconf.start_wifi():
					errors.append("Can't start WIFI network!")

			elif wifi_mode == "hotspot":
				if not zynconf.start_wifi_hotspot():
					errors.append("Can't start WIFI Hotspot!")

			else:
				if not zynconf.stop_wifi():
					errors.append("Can't stop WIFI!")

		except Exception as e:
			errors.append(e)

		self.get(errors)


	def read_supplicant_data(self):
		try:
			fo = open(self.wpa_supplicant_config_fpath, "r")
			wpa_supplicant_data = "".join(fo.readlines())
			fo.close()
			return wpa_supplicant_data
		except:
			pass
		return ""


	def apply_updated_fields(self, wpa_supplicant_data, fieldNames):
		previous_supplicant_data = self.read_supplicant_data()

		p = re.compile('.*?network=\\{.*?ssid=\\"(.*?)\\".*?psk=\\"(.*?)\\".*?\\}.*?', re.I | re.M | re.S )
		iterator = p.finditer(previous_supplicant_data)
		for m in iterator:
			action = self.get_argument('ZYNTHIAN_WIFI_ACTION')
			if action and action == 'REMOVE_' + m.group(1):
				print('Removing network')
				pRemove =  re.compile('(.*)network={.*?ssid=\\"' + m.group(1) + '\\".*?}(.*)', re.I | re.M | re.S )
				wpa_supplicant_data = pRemove.sub(r'\1\2', wpa_supplicant_data)
			else:
				newPassword =  self.get_argument('ZYNTHIAN_WIFI_PSK_' + m.group(1))

				mNewSupplicantData = re.match('.*ssid="' + m.group(1) + '".*?psk="(.*?)".*', wpa_supplicant_data, re.I | re.M | re.S)
				if mNewSupplicantData:
					if not newPassword and  not mNewSupplicantData.group(1) == WifiConfigHandler.passwordMask:
						newPassword = mNewSupplicantData.group(1)
				if not newPassword: newPassword = m.group(2)

				pReplacePasswordVeil = re.compile('ssid=\\"' + m.group(1) + '\\"(.*?psk=)\\".*?\\"', re.I | re.M | re.S )
				wpa_supplicant_data = pReplacePasswordVeil.sub('ssid="' + m.group(1) + r'"\1"' + newPassword + '"', wpa_supplicant_data)

				for fieldName in fieldNames:
					fieldUpdated =  self.get_argument(fieldName + '_' + m.group(1) + '_UPDATED')
					if fieldUpdated:
						fieldValue =  self.get_argument(fieldName + '_' + m.group(1))
						regexp = 'ssid=\\"' + m.group(1) + '\\"(?P<pre>.*?' + self.fieldMap[fieldName] + '=)\\S+(?P<post>.*\\})'
						pReplacement = re.compile(regexp, re.I | re.M | re.S )
						wpa_supplicant_data = pReplacement.sub("ssid=\"" + m.group(1) + "\"" + r'\g<pre>' + str(fieldValue) + r'\g<post> ', wpa_supplicant_data)

		return wpa_supplicant_data


	def add_new_network(self, wpa_supplicant_data, newSSID):
		wpa_supplicant_data += '\nnetwork={\n\tssid="'
		wpa_supplicant_data += newSSID
		wpa_supplicant_data += '"\n\tscan_ssid=1\n\tkey_mgmt=WPA-PSK\n\tpsk=""\n\tpriority=10\n}'
		return wpa_supplicant_data
