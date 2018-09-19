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
import glob
from xml.etree import ElementTree as ET
from collections import OrderedDict

from lib.zynthian_config_handler import ZynthianConfigHandler
from zyngine.zynthian_engine_pianoteq import *

#------------------------------------------------------------------------------
# Jalv LV2 Configuration
#------------------------------------------------------------------------------

class JalvLv2Handler(ZynthianConfigHandler):
	JALV_LV2_CONFIG_FILE = "$ZYNTHIAN_CONFIG_DIR/jalv_plugins.json"

	@tornado.web.authenticated
	def get(self, errors=None):
		config=OrderedDict([])
		config['ZYNTHIAN_JALV_PLUGINS'] = self.load_plugins()

		if self.genjson:
			self.write(config)
		else:
			if errors:
				logging.error("Configuring JALV / LV2  failed: %s" % format(errors))
				self.clear()
				self.set_status(400)
				self.finish("Configuring JALV / LV2  failed: %s" % format(errors))
			else:
				self.render("config.html", body="jalv_lv2.html", config=config, title="JALV / LV2 Plugins", errors=errors)

	@tornado.web.authenticated
	def post(self):
		action = self.get_argument('ZYNTHIAN_JALV_ACTION')
		if action:
			errors = {
				'INSTALL_LV2_PLUGINS': lambda: self.do_install_jalv()
			}[action]()
		self.get(errors)


	def load_plugins(self):
		result = OrderedDict([
			['Dexed', {'URL': 'https://github.com/dcoredump/dexed.lv2', 'INSTALLED': True}],
			['Helm', {'URL': 'http://tytel.org/hel', 'INSTALLED': True}],
			['SuperDooper', {'URL': 'http://acme.com', 'INSTALLED': False}]
		])
		return result

	def do_install_jalv(self):

		try:
			logging.info("Not implemented yet")

		except Exception as e:
			logging.error("Installing jalv plugins failed: %s" % format(e))
			return format(e)

