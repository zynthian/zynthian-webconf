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
import re
import logging
import tornado.web
from crypt import crypt
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
			['CURRENT_PASSWORD', {
				'type': 'password',
				'title': 'Current password',
				'value': '*'
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

		super().get("Security/Access", config, errors)


	@tornado.web.authenticated
	def post(self):
		params=tornado.escape.recursive_unicode(self.request.arguments)
		logging.debug("COMMAND: %s" % params['_command'][0])
		if params['_command'][0]=="REGENERATE_KEYS":
			cmd=os.environ.get('ZYNTHIAN_SYS_DIR') + "/sbin/regenerate_keys.sh"
			check_output(cmd, shell=True)
			self.redirect('/sys-reboot')
		else:
			errors=self.update_system_config(params)
			self.get(errors)


	def update_system_config(self, config):
		#Update Password
		current_passwd = self.get_argument("CURRENT_PASSWORD")
		try:
			root_crypt = check_output("getent shadow root", shell=True).decode("utf-8").split(':')[1]
			rcparts = root_crypt.split('$')
			current_crypt = crypt(current_passwd, "$%s$%s" % (rcparts[1], rcparts[2]))

			logging.debug("PASSWD: %s <=> %s" % (root_crypt, current_crypt))
			if current_crypt != root_crypt:
				return {'CURRENT_PASSWORD': "Current password is not correct"}
		except:
			return {'CURRENT_PASSWORD': "Current password is not correct"}

		if len(config['PASSWORD'][0])>0:
			if len(config['PASSWORD'][0])<6:
				return { 'PASSWORD': "Password must have at least 6 characters" }
			if config['PASSWORD'][0]!=config['REPEAT_PASSWORD'][0]:
				return { 'REPEAT_PASSWORD': "Passwords does not match!" }
			try:
				check_output(['usermod', '-p', crypt(config['PASSWORD'][0]), 'root'])
			except Exception as e:
				logging.error("Can't set new password! => {}".format(e))
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
				#contents = contents.replace(previousHostname, newHostname)
				contents = re.sub(r"127\.0\.1\.1.*$", "127.0.1.1\t{}".format(newHostname), contents)
				f.seek(0)
				f.truncate()
				f.write(contents)
				f.close()

			check_output(["hostnamectl", "set-hostname", newHostname])

			#self.reboot_flag=True
