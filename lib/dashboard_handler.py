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
import uuid
import re
import logging
import tornado.web
import json
import shutil
import requests
from collections import OrderedDict

from lib.ZynthianConfigHandler import ZynthianConfigHandler
from lib.SecurityConfigHandler import SecurityConfigHandler
from lib.SnapshotConfigHandler import SnapshotConfigHandler
from lib.soundfont_config_handler import SoundfontConfigHandler
from lib.presets_config_handler import PresetsConfigHandler



#------------------------------------------------------------------------------
# Soundfont Configuration
#------------------------------------------------------------------------------

class DashboardHandler(tornado.web.RequestHandler):

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
		config=OrderedDict([
			['Hostname', {
				'url': '/api/sys-security',
				'name': SecurityConfigHandler.get_host_name(),
			}],
			['Display', {
				'url': '/api/hw-display',
				'name': os.environ.get('DISPLAY_NAME'),
			}],
			['Audio', {
				'url': '/api/hw-audio',
				'name': os.environ.get('SOUNDCARD_NAME'),
			}],
			['Wiring', {
				'url':'/api/hw-wiring',
				'name': os.environ.get('ZYNTHIAN_WIRING_LAYOUT'),
			}],
			['MIDI profile', {
				'url':'/api/ui-midi',
				'name': os.environ.get('ZYNTHIAN_SCRIPT_MIDI_PROFILE'),
			}],
			['Snapshots', {
				'url':'/api/lib-snapshot',
				'name': self.get_directory_summary(SnapshotConfigHandler.SNAPSHOTS_DIRECTORY),
			}],
			['Soundfonts', {
				'url':'/api/lib-soundfont',
				'name': self.get_directory_summary(SoundfontConfigHandler.SOUNDFONTS_DIRECTORY),
			}],
			['Presets', {
				'url':'/api/lib-presets',
				'name': self.get_directory_summary(PresetsConfigHandler.PRESETS_DIRECTORY),
			}],


		])

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="dashboard.html", config=config, title="Dashboard", errors=errors)

	def get_directory_summary(self, directory):
		result = []
		for pack in os.walk(directory):
			for f in pack[2]:
				result.append(f)

		fileList =  os.listdir(directory)
		fileList = sorted(fileList)
		return '<br /> '.join(result)
