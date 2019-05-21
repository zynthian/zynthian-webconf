# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Security Configuration Handler
#
# Copyright (C) 2017 Fernando Moyano <jofemodo@zynthian.org>
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
import logging
import tornado.web
from collections import OrderedDict
from subprocess import check_output

from lib.zynthian_config_handler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# System Menu
#------------------------------------------------------------------------------

class SecurityConfigHandler(ZynthianConfigHandler):

	@staticmethod
	def get_host_name():
		with open("/etc/hostname") as f:
			return f.readline()


	@tornado.web.authenticated
	def get(self, errors=None):
		#Get Hostname
		config=OrderedDict([
			['PASSWORD', {
				'type': 'password',
				'title': 'Password',
				'value': '*'
			}],
			['REPEAT_PASSWORD', {
				'type': 'password',
				'title': 'Repeat password',
				'value': '*'
			}],
			['HOSTNAME', {
				'type': 'text',
				'title': 'Hostname',
				'value': SecurityConfigHandler.get_host_name(),
				'advanced': True
			}],
			['REGENERATE_KEYS', {
				'type': 'button',
				'title': 'Regenerate Keys',
				'script_file': 'regenerate_keys.js',
				'button_type': 'button',
				'class': 'btn-warning btn-block',
				'advanced': True
			}],
			['_command', {
				'type': 'hidden',
				'value': ''
			}]
		])
		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="config_block.html", config=config, title="Security/Access", errors=errors)


	@tornado.web.authenticated
	def post(self):
		params=tornado.escape.recursive_unicode(self.request.arguments)
		logging.debug("COMMAND: %s" % params['_command'][0])
		if params['_command'][0]=="REGENERATE_KEYS":
			cmd=os.environ.get('ZYNTHIAN_SYS_DIR') + "/sbin/regenerate_keys.sh"
			check_output(cmd, shell=True)
			self.redirect('/api/sys-reboot')
		else:
			errors=self.update_system_config(params)
			self.get(errors)


	def update_system_config(self, config):
		#Update Password
		if len(config['PASSWORD'][0])>0:
			if len(config['PASSWORD'][0])<6:
				return { 'PASSWORD': "Password must have at least 6 characters" }
			if config['PASSWORD'][0]!=config['REPEAT_PASSWORD'][0]:
				return { 'REPEAT_PASSWORD': "Passwords does not match!" }
			try:
				esc_passwd=config['PASSWORD'][0].replace('"','\\"').replace('$','\\$').replace('`','\\`')
				check_output("echo -e \"root:{}\" | chpasswd".format(esc_passwd), shell=True, executable="/bin/bash")
			except Exception as e:
				return { 'REPEAT_PASSWORD': "Can't set new password!" }
			

		#Update Hostname
		newHostname = config['HOSTNAME'][0]
		previousHostname = ''
		with open("/etc/hostname",'r') as f:
			previousHostname=f.readline()
			f.close()

		if previousHostname!=newHostname:
			with open("/etc/hostname",'w') as f:
				f.write(newHostname)
				f.close()

			with open("/etc/hosts", "r+") as f:
				contents = f.read()
				contents = contents.replace(previousHostname, newHostname)
				contents = contents.replace("zynthian", newHostname) # for the ppl that have already changed their hostname
				f.seek(0)
				f.truncate()
				f.write(contents)
				f.close()

