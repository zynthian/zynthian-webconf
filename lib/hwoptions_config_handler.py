# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Hardware Options Configuration Handler
#
# Copyright (C) 2022 Fernando Moyano <jofemodo@zynthian.org>
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
from lib.zynthian_config_handler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# Audio Configuration Class
#------------------------------------------------------------------------------

class HWOptionsConfigHandler(ZynthianConfigHandler):

	@tornado.web.authenticated
	def get(self, errors=None):

		config=OrderedDict()

		config['ZYNTHIAN_DISABLE_OTG'] = {
			'type': 'boolean',
			'title': "Disable OTG",
			'value': os.environ.get('ZYNTHIAN_DISABLE_OTG','0'),
			'advanced': False
		}
		config['ZYNTHIAN_LIMIT_USB_SPEED'] = {
			'type': 'boolean',
			'title': "Limit USB speed to 12Mb/s",
			'value': os.environ.get('ZYNTHIAN_LIMIT_USB_SPEED','0'),
			'advanced': False
		}
		config['ZYNTHIAN_OVERCLOCKING'] = {
			'type': 'select',
			'title': "Overclocking",
			'value': os.environ.get('ZYNTHIAN_OVERCLOCKING','None'),
			'options': ['None', 'Medium', 'Maximum'],
			'advanced': True
		}
		config['ZYNTHIAN_CUSTOM_CONFIG'] = {
			'type': 'textarea',
			'title': "Custom Config",
			'cols': 50,
			'rows': 6,
			'value': os.environ.get('ZYNTHIAN_CUSTOM_CONFIG'),
			'advanced': True
		}
		config['ZYNTHIAN_CUSTOM_BOOT_CMDLINE'] = {
			'type': 'text',
			'title': "Custom Boot Command",
			'value': os.environ.get('ZYNTHIAN_CUSTOM_BOOT_CMDLINE'),
			'advanced': True
		}
		config['_SPACER_'] = {
			'type': 'html',
			'content': "<br>"
		}

		super().get("Hardware Options", config, errors)


	@tornado.web.authenticated
	def post(self):
		self.request.arguments['ZYNTHIAN_LIMIT_USB_SPEED'] = self.request.arguments.get('ZYNTHIAN_LIMIT_USB_SPEED', '0')
		self.request.arguments['ZYNTHIAN_DISABLE_OTG'] = self.request.arguments.get('ZYNTHIAN_DISABLE_OTG', '0')
		self.request.arguments['ZYNTHIAN_OVERCLOCKING'] = self.request.arguments.get('ZYNTHIAN_OVERCLOCKING', '0')

		postedConfig = tornado.escape.recursive_unicode(self.request.arguments)

		command = self.get_argument('_command', '')
		logging.info("COMMAND = {}".format(command))

		if command=='REFRESH':
			errors = None
			self.config_env(postedConfig)
		else:
			errors=self.update_config(postedConfig)
			self.reboot_flag = True

		self.get(errors)

