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
			self.render("config.html", body="config_block.html", config=config, title="Security/Access", errors=errors)

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
		previousHostname = ''
		with open("/etc/hostname",'r') as f:
			previousHostname=f.readline()
			f.close()

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
