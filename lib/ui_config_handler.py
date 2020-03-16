# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# UI Configuration Handler
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

from lib.zynthian_config_handler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# UI Configuration
#------------------------------------------------------------------------------

class UiConfigHandler(ZynthianConfigHandler):

	font_families=[
		"Audiowide",
		"Helvetica",
		"Economica",
		"Orbitron",
		"Abel"
	]

	@tornado.web.authenticated
	def get(self, errors=None):
		config=OrderedDict([
			['ZYNTHIAN_UI_FONT_SIZE', {
				'type': 'text',
				'title': 'Font Size',
				'value': os.environ.get('ZYNTHIAN_UI_FONT_SIZE')
			}],
			['ZYNTHIAN_UI_FONT_FAMILY', {
				'type': 'select',
				'title': 'Font Family',
				'value': os.environ.get('ZYNTHIAN_UI_FONT_FAMILY'),
				'options': self.font_families,
				'advanced': True
			}],
			['ZYNTHIAN_UI_COLOR_BG', {
				'type': 'text',
				'title': 'Background Color',
				'value': os.environ.get('ZYNTHIAN_UI_COLOR_BG'),
				'advanced': True
			}],
			['ZYNTHIAN_UI_COLOR_TX', {
				'type': 'text',
				'title': 'Text Color',
				'value': os.environ.get('ZYNTHIAN_UI_COLOR_TX'),
				'advanced': True
			}],
			['ZYNTHIAN_UI_COLOR_ON', {
				'type': 'text',
				'title': 'Light Color',
				'value': os.environ.get('ZYNTHIAN_UI_COLOR_ON'),
				'advanced': True
			}],
			['ZYNTHIAN_UI_COLOR_PANEL_BG', {
				'type': 'text',
				'title': 'Panel Background Color',
				'value': os.environ.get('ZYNTHIAN_UI_COLOR_PANEL_BG'),
				'advanced': True
			}],
			['ZYNTHIAN_UI_METER_SELECTION', {
				'type': 'select',
				'title': 'Meter',
				'value':  'CPU Usage' if os.environ.get('ZYNTHIAN_UI_SHOW_CPU_STATUS')=='1' else 'Audio Level',
				'options': ['Audio Level', 'CPU Usage'],
				'option_labels': {
					'Audio Level': 'Audio Level',
					'CPU Usage': 'CPU Usage', # these option_labels are2 needed, because otherwise 'Cpu Usage' is generatted
				}
			}],
			['ZYNTHIAN_UI_RESTORE_LAST_STATE', {
				'type': 'boolean',
				'title': 'Restore last state on startup',
				'value': os.environ.get('ZYNTHIAN_UI_RESTORE_LAST_STATE', '1')
			}],
			['ZYNTHIAN_UI_SNAPSHOT_MIXER_SETTINGS', {
				'type': 'boolean',
				'title': 'Mixer settings on snapshots',
				'value': os.environ.get('ZYNTHIAN_UI_SNAPSHOT_MIXER_SETTINGS', '0')
			}],
			['ZYNTHIAN_UI_ENABLE_CURSOR', {
				'type': 'boolean',
				'title': 'Enable cursor',
				'value': os.environ.get('ZYNTHIAN_UI_ENABLE_CURSOR', '0'),
				'advanced': True
			}]
		])

		super().get("User Interface", config, errors)


	@tornado.web.authenticated
	def post(self):
		self.request.arguments['ZYNTHIAN_UI_SNAPSHOT_MIXER_SETTINGS'] = self.request.arguments.get('ZYNTHIAN_UI_SNAPSHOT_MIXER_SETTINGS', '0')
		self.request.arguments['ZYNTHIAN_UI_RESTORE_LAST_STATE'] = self.request.arguments.get('ZYNTHIAN_UI_RESTORE_LAST_STATE', '0')
		self.request.arguments['ZYNTHIAN_UI_ENABLE_CURSOR'] = self.request.arguments.get('ZYNTHIAN_UI_ENABLE_CURSOR', '0')

		escaped_arguments = tornado.escape.recursive_unicode(self.request.arguments)

		if escaped_arguments['ZYNTHIAN_UI_METER_SELECTION'][0]=='CPU Usage':
			escaped_arguments['ZYNTHIAN_UI_SHOW_CPU_STATUS'] = '1'
		else:
			escaped_arguments['ZYNTHIAN_UI_SHOW_CPU_STATUS'] = '0'

		del escaped_arguments['ZYNTHIAN_UI_METER_SELECTION']

		errors=self.update_config(escaped_arguments)

		self.restart_ui_flag = True
		self.get(errors)
