import os
import re
import tornado.web
from collections import OrderedDict


#------------------------------------------------------------------------------
# Wifi Config Handler
#------------------------------------------------------------------------------

class WifiConfigHandler(tornado.web.RequestHandler):

	fieldMap = {"ZYNTHIAN_WIFI_PRIORITY": "priority"}

	def get_current_user(self):
		return self.get_secure_cookie("user")

	def prepare(self):
		self.genjson=False
		try:
			if self.get_query_argument("json"):
				self.genjson=True
		except:
			pass

	@tornado.web.authenticated
	def get(self, errors=None):
		supplicant_file_name = self.getSupplicantFileName()
		supplicant_data = re.sub(r'psk=".*?"', 'psk="*****"',
			self.readSupplicantData(supplicant_file_name),
			re.IGNORECASE | re.MULTILINE | re.DOTALL )
		p = re.compile('.*?network=\\{.*?ssid=\\"(.*?)\\".*?psk=\\"(.*?)\\".*?priority=(\d*).*?\\}.*?', re.IGNORECASE | re.MULTILINE | re.DOTALL )
		iterator = p.finditer(supplicant_data)
		config=OrderedDict([
			['ZYNTHIAN_WIFI_WPA_SUPPLICANT', {
				'type': 'textarea',
				'cols': 50,
				'rows': 20,
				'title': 'Advanced Config',
				'value': supplicant_data
			}]
		])

		networks = []
		idx = 0
		for m in iterator:
			networks.append({
			    'idx': idx,
				'ssid': m.group(1),
				'psk': m.group(2),
				'priority': m.group(3)
			})
			idx+=1

		config['ZYNTHIAN_WIFI_NETWORKS'] = networks

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="wifi.html", config=config, title="Wifi", errors=errors)


	def post(self):
		wpa_supplicant_data = self.get_argument('ZYNTHIAN_WIFI_WPA_SUPPLICANT')
		fieldNames = ["ZYNTHIAN_WIFI_PRIORITY"]
		wpa_supplicant_data = self.applyUpdatedFields(wpa_supplicant_data, fieldNames)

		newSSID =  self.get_argument('ZYNTHIAN_WIFI_NEW_SSID')
		if newSSID: wpa_supplicant_data = self.addNewNetwork(wpa_supplicant_data, newSSID)

		fo = open("/etc/wpa_supplicant/wpa_supplicant.conf", "w")
		fo.write(wpa_supplicant_data)
		fo.flush()
		fo.close()
		errors=self.get()

	def getSupplicantFileName(self):
		supplicant_file_name = "/etc/wpa_supplicant/wpa_supplicant.conf"
		#if os.path.getsize(supplicant_file_name) == 0:
		#	supplicant_file_name = "/zynthian/zynthian-sys/etc/wpa_supplicant/wpa_supplicant.conf"
		return supplicant_file_name

	def readSupplicantData(self, supplicant_file_name):
		fo = open(supplicant_file_name, "r")
		wpa_supplicant_data = "".join(fo.readlines())
		fo.close()
		return wpa_supplicant_data

	def applyUpdatedFields(self, wpa_supplicant_data, fieldNames):
		supplicant_file_name = self.getSupplicantFileName()
		previous_supplicant_data = self.readSupplicantData(supplicant_file_name)

		p = re.compile('.*?network=\\{.*?ssid=\\"(.*?)\\".*?psk=\\"(.*?)\\".*?\\}.*?', re.IGNORECASE | re.MULTILINE | re.DOTALL )
		iterator = p.finditer(previous_supplicant_data)
		for m in iterator:
			action = self.get_argument('ZYNTHIAN_WIFI_ACTION')
			if action and action == 'REMOVE_' + m.group(1):
				print('Removing network')
				pRemove =  re.compile('(.*)network={.*?ssid=\\"' + m.group(1) + '\\".*?}(.*)', re.IGNORECASE | re.MULTILINE | re.DOTALL )
				wpa_supplicant_data = pRemove.sub(r'\1\2', wpa_supplicant_data)
			else:
				newPassword =  self.get_argument('ZYNTHIAN_WIFI_PSK_' + m.group(1))
				if not newPassword: newPassword = m.group(2)

				pReplacePasswordVeil = re.compile('ssid=\\"' + m.group(1) + '\\"(.*?psk=)\\".*?\\"', re.IGNORECASE | re.MULTILINE | re.DOTALL )
				wpa_supplicant_data = pReplacePasswordVeil.sub('ssid="' + m.group(1) + r'"\1"' + newPassword + '"', wpa_supplicant_data)

				for fieldName in fieldNames:
					fieldUpdated =  self.get_argument(fieldName + '_' + m.group(1) + '_UPDATED')
					if fieldUpdated:
						fieldValue =  self.get_argument(fieldName + '_' + m.group(1))
						regexp = 'ssid=\\"' + m.group(1) + '\\"(?P<pre>.*?' + self.fieldMap[fieldName] + '=)\\S+(?P<post>.*\\})'
						pReplacement = re.compile(regexp, re.IGNORECASE | re.MULTILINE | re.DOTALL )
						wpa_supplicant_data = pReplacement.sub("ssid=\"" + m.group(1) + "\"" + r'\g<pre>' + str(fieldValue) + r'\g<post> ', wpa_supplicant_data)

		return wpa_supplicant_data

	def addNewNetwork(self, wpa_supplicant_data, newSSID):
		wpa_supplicant_data += '\nnetwork={\n\tssid="'
		wpa_supplicant_data += newSSID
		wpa_supplicant_data += '"\n\tscan_ssid=1\n\tkey_mgmt=WPA-PSK\n\tpsk=""\n\tpriority=10\n}'
		return wpa_supplicant_data
