# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Audio Configuration Handler
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
from collections import OrderedDict
from subprocess import check_output, call
from lib.zynthian_config_handler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# Kit Configuration
#------------------------------------------------------------------------------

class KitConfigHandler(ZynthianConfigHandler):

	kit_presets=OrderedDict([
		['V3', {
			'KIT_DESCRIPTION': 'Description V3'
		}],
		['V2+', {
			'KIT_DESCRIPTION': 'Description V2+'
		}],
		['V2', {
			'KIT_DESCRIPTION': 'Description V2'
		}],
		['V1', {
			'KIT_DESCRIPTION': 'Description V1'
		}],
		['Custom', {
			'KIT_DESCRIPTION': 'Description Custom'
		}]
	])

	@tornado.web.authenticated
	def get(self, errors=None):
		selected_kit = os.environ.get('ZYNTHIAN_KIT_VERSION')
		if not selected_kit:
			selected_kit = 'V2+'

		config=OrderedDict([
			['ZYNTHIAN_KIT_VERSION', {
				'type': 'select',
				'title': 'Kit',
				'value': selected_kit,
				'options': list(self.kit_presets.keys()),
				'presets': self.kit_presets
			}],
			['KIT_DESCRIPTION', {
				'type': 'textarea',
				'value': self.kit_presets[selected_kit]['KIT_DESCRIPTION'],
				'title': 'Description',
				'cols': 50,
				'rows': 5

			}]

		])

		logging.info(config)
		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="config_block.html", config=config, title="Kit", errors=errors)


	@tornado.web.authenticated
	def post(self):
		postedConfig = tornado.escape.recursive_unicode(self.request.arguments)
		del postedConfig['KIT_DESCRIPTION']
		errors=self.update_config(postedConfig)
		self.redirect('/api/sys-reboot')
		self.get(errors)


	def needs_reboot(self):
		return True
