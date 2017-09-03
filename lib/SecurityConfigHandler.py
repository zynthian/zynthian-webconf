import os
import logging
import tornado.web
from collections import OrderedDict
from subprocess import check_output
from lib.ZynthianConfigHandler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# System Menu
#------------------------------------------------------------------------------

class SecurityConfigHandler(ZynthianConfigHandler):

	@tornado.web.authenticated
	def get(self, errors=None):
		#Get Hostname
		with open("/etc/hostname") as f:
			hostname=f.readline()

		config=OrderedDict([
			['HOSTNAME', {
				'type': 'text',
				'title': 'Hostname',
				'value': hostname
			}],
			['PASSWORD', {
				'type': 'password',
				'title': 'Password',
				'value': '*'
			}],
			['REPEAT_PASSWORD', {
				'type': 'password',
				'title': 'Repeat password',
				'value': '*'
			}]
		])
		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="config_block.html", config=config, title="User", errors=errors)

	def post(self):
		errors=self.update_system_config(tornado.escape.recursive_unicode(self.request.arguments))
		self.get(errors)

	def update_system_config(self, config):
		#Update Password
		if len(config['PASSWORD'][0])<6:
			return { 'PASSWORD': "Password must have at least 6 characters" }
		if config['PASSWORD'][0]!=config['REPEAT_PASSWORD'][0]:
			return { 'REPEAT_PASSWORD': "Passwords does not match!" }
		check_output("echo root:%s | chpasswd" % config['PASSWORD'][0], shell=True)

		#Update Hostname
		newHostname = config['HOSTNAME'][0]
		with open("/etc/hostname",'r') as f:
			previousHostname=f.readline()
			f.close()

		with open("/etc/hostname",'w') as f:
			f.write(newHostname)
			f.close()

		with open("/etc/hosts", "r+") as f:
			contents = f.read()
			contents.replace(previousHostname, newHostname)
			contents.replace("zynthian", newHostname)
			f.seek(0)
			f.truncate()
			f.write(contents)
			f.close()
