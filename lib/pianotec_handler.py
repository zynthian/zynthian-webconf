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
import tarfile

from collections import OrderedDict

from lib.ZynthianConfigHandler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# Soundfont Configuration
#------------------------------------------------------------------------------

class PianotecHandler(tornado.web.RequestHandler):

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
			self.render("config.html", body="pianotec.html", config=config, title="Pianoteq", errors=errors)

	def post(self):
		action = self.get_argument('ZYNTHIAN_PIANOTEC_ACTION')
		if action:
			errors = {
        		'INSTALL_PIANOTEC': lambda: self.do_install_pianotec()
    		}[action]()


		self.get(errors)

	def do_install_pianotec(self):
		filename = self.get_argument('ZYNTHIAN_PIANOTEC_FILENAME');
		logging.info(filename)
		tar = tarfile.open(filename, "r:gz")
		for member in tar.getmembers():
			logging.info(member)
			tar.extract(member, "/")
		tar.close()
