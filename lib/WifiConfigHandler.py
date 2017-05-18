import os
import re
import tornado.web
from collections import OrderedDict


#------------------------------------------------------------------------------
# Wifi Config Handler
#------------------------------------------------------------------------------

class WifiConfigHandler(tornado.web.RequestHandler):
	def prepare(self):
		self.genjson=False
		try:
			if self.get_query_argument("json"):
				self.genjson=True
		except:
			pass


	def get(self, errors=None):
		supplicant_file_name = self.getSupplicantFileName()
		supplicant_data = self.readSupplicantData(supplicant_file_name)
		p = re.compile('.*?network=\\{.*?ssid=\\"(.*?)\\".*?psk=\\"(.*?)\\".*?priority=(\d*).*?\\}.*?', re.IGNORECASE | re.MULTILINE | re.DOTALL )
		iterator = p.finditer(supplicant_data)
		config=OrderedDict([
			['ZYNTHIAN_WIFI_WPA_SUPPLICANT', {
				'type': 'textarea',
				'cols': 50,
				'rows': 20,
				'title': '/etc/wpa_supplicant/wpa_supplicant.conf',
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

		print(networks)

		config['ZYNTHIAN_WIFI_NETWORKS'] = networks

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="wifi.html", config=config, title="Wifi", errors=errors)


	def post(self):
		fo = open("/etc/wpa_supplicant/wpa_supplicant.conf", "w")
		wpa_supplicant_data = self.get_argument('ZYNTHIAN_WIFI_WPA_SUPPLICANT')
		fo.write(wpa_supplicant_data)
		fo.flush()
		fo.close()
		errors=self.get()

	def getSupplicantFileName(self):
		supplicant_file_name = "/etc/wpa_supplicant/wpa_supplicant.conf"
		if os.path.getsize(supplicant_file_name) == 0:
			supplicant_file_name = "/zynthian/zynthian-sys/etc/wpa_supplicant/wpa_supplicant.conf"
		return supplicant_file_name

	def readSupplicantData(self, supplicant_file_name):
		fo = open(supplicant_file_name, "r")
		wpa_supplicant_data = "".join(fo.readlines())
		fo.close()
		return wpa_supplicant_data
