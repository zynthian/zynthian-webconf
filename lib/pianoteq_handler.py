# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Presets Manager Handler
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
import logging
import tornado.web
import json
import requests
import subprocess
import shlex
import shutil

from collections import OrderedDict

from lib.ZynthianConfigHandler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# Soundfont Configuration
#------------------------------------------------------------------------------

class PianoteqHandler(tornado.web.RequestHandler):

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
		config=OrderedDict([])
		config['ZYNTHIAN_UPLOAD_MULTIPLE'] = False
		errors = {}

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="pianoteq.html", config=config, title="Pianoteq", errors=errors)

	def post(self):
		action = self.get_argument('ZYNTHIAN_PIANOTEQ_ACTION')
		if action:
			errors = {
        		'INSTALL_PIANOTEQ': lambda: self.do_install_pianoteq()
    		}[action]()


		self.get(errors)

	def do_install_pianoteq(self):
		filename = self.get_argument('ZYNTHIAN_PIANOTEQ_FILENAME');
		logging.info("Installing %s" % filename)

		# Just to be sure...
		if(os.path.isdir("/tmp/pianoteq")):
			shutil.rmtree("/tmp/pianoteq")
		if(not os.path.isdir("/zynthian/zynthian-sw/pianoteq6")):
			os.mkdir("/zynthian/zynthian-sw/pianoteq6")

		# Install binary
		subprocess.call(shlex.split("/usr/bin/7z x -o/tmp/pianoteq %s \"Pianoteq 6 STAGE/arm/Pianoteq 6 STAGE*\"" % filename))
		if(os.path.isfile("/zynthian/zynthian-sw/pianoteq6/Pianoteq 6 STAGE")):
			logging.info("Removing old pianoteq binary")
			os.remove("/zynthian/zynthian-sw/pianoteq6/Pianoteq 6 STAGE")
		logging.info("Installing new pianoteq binary")
		shutil.move("/tmp/pianoteq/Pianoteq 6 STAGE/arm/Pianoteq 6 STAGE","/zynthian/zynthian-sw/pianoteq6/")

		# Install LV2 plugin
		if(os.path.isdir("/zynthian/zynthian-sw/pianoteq6/Pianoteq 6 STAGE.lv2")):
			logging.info("Removing old pianoteq LV2 plugin")
			shutil.rmtree("/zynthian/zynthian-sw/pianoteq6/Pianoteq 6 STAGE.lv2")
		logging.info("Installing new pianoteq LV2 plugin")
		shutil.move("/tmp/pianoteq/Pianoteq 6 STAGE/arm/Pianoteq 6 STAGE.lv2","/zynthian/zynthian-sw/pianoteq6/")
		if(os.path.islink("/zynthian/zynthian-plugins/lv2/Pianoteq 6 STAGE.lv2")):
			os.unlink("/zynthian/zynthian-plugins/lv2/Pianoteq 6 STAGE.lv2")
		elif(os.path.isdir("/zynthian/zynthian-plugins/lv2/Pianoteq 6 STAGE.lv2")):
			shutil.rmtree("/zynthian/zynthian-plugins/lv2/Pianoteq 6 STAGE.lv2")
		else:
			os.remove("/zynthian/zynthian-plugins/lv2/Pianoteq 6 STAGE.lv2")
		os.symlink("/zynthian/zynthian-sw/pianoteq6/Pianoteq 6 STAGE.lv2","/zynthian/zynthian-plugins/lv2/Pianoteq 6 STAGE.lv2")

		# Cover my tracks
		if(os.path.isdir("/tmp/pianoteq")):
			shutil.rmtree("/tmp/pianoteq")
