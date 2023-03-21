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
			['ZYNTHIAN_UI_SWITCH_BOLD_MS', {
				'type': 'text',
				'title': 'Bold Push Time (ms)',
				'value': os.environ.get('ZYNTHIAN_UI_SWITCH_BOLD_MS', '300'),
				'advanced': True
			}],
			['ZYNTHIAN_UI_SWITCH_LONG_MS', {
				'type': 'text',
				'title': 'Long Push Time (ms)',
				'value': os.environ.get('ZYNTHIAN_UI_SWITCH_LONG_MS', '2000'),
				'advanced': True
			}],
			['ZYNTHIAN_UI_VISIBLE_MIXER_STRIPS', {
				'type': 'select',
				'title': 'Visible mixer strips',
				'value':  os.environ.get('ZYNTHIAN_UI_VISIBLE_MIXER_STRIPS'),
				'options': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16'],
				'option_labels': {
					'0': 'Automatic',
					'1': '1',
					'2': '2',
					'3': '3',
					'4': '4',
					'5': '5',
					'6': '6',
					'7': '7',
					'8': '8',
					'9': '9',
					'10': '10',
					'11': '11',
					'12': '12',
					'13': '13',
					'14': '14',
					'15': '15',
					'16': '16'
				},
				'advanced': True
			}],
			['ZYNTHIAN_UI_POWER_SAVE_MINUTES', {
				'type': 'text',
				'title': 'Power Save Delay (minutes)',
				'value': os.environ.get('ZYNTHIAN_UI_POWER_SAVE_MINUTES', '60'),
				'advanced': True
			}],
			['ZYNTHIAN_UI_RESTORE_LAST_STATE', {
				'type': 'boolean',
				'title': 'Restore last state on startup',
				'value': os.environ.get('ZYNTHIAN_UI_RESTORE_LAST_STATE', '1')
			}],
			['ZYNTHIAN_UI_SNAPSHOT_MIXER_SETTINGS', {
				'type': 'boolean',
				'title': 'Audio Levels on Snapshots',
				'value': os.environ.get('ZYNTHIAN_UI_SNAPSHOT_MIXER_SETTINGS', '0')
			}],
			['ZYNTHIAN_UI_ONSCREEN_BUTTONS', {
				'type': 'boolean',
				'title': 'Enable Onscreen Buttons',
				'value': os.environ.get('ZYNTHIAN_UI_ONSCREEN_BUTTONS', '0'),
			}],
			['ZYNTHIAN_UI_MULTICHANNEL_RECORDER', {
				'type': 'boolean',
				'title': 'Enable Multichannel Recording',
				'value': os.environ.get('ZYNTHIAN_UI_MULTICHANNEL_RECORDER', '0'),
			}],
			['ZYNTHIAN_UI_ENABLE_CURSOR', {
				'type': 'boolean',
				'title': 'Enable cursor',
				'value': os.environ.get('ZYNTHIAN_UI_ENABLE_CURSOR', '0'),
				'advanced': True
			}],
			['ZYNTHIAN_VNCSERVER_ENABLED', {
				'type': 'boolean',
				'title': 'Enable VNC Server',
				'value': os.environ.get('ZYNTHIAN_VNCSERVER_ENABLED', '0'),
			}]
		])

		super().get("User Interface", config, errors)


	@tornado.web.authenticated
	def post(self):
		self.request.arguments['ZYNTHIAN_UI_SNAPSHOT_MIXER_SETTINGS'] = self.request.arguments.get('ZYNTHIAN_UI_SNAPSHOT_MIXER_SETTINGS', '0')
		self.request.arguments['ZYNTHIAN_UI_RESTORE_LAST_STATE'] = self.request.arguments.get('ZYNTHIAN_UI_RESTORE_LAST_STATE', '0')
		self.request.arguments['ZYNTHIAN_UI_ENABLE_CURSOR'] = self.request.arguments.get('ZYNTHIAN_UI_ENABLE_CURSOR', '0')
		self.request.arguments['ZYNTHIAN_UI_ONSCREEN_BUTTONS'] = self.request.arguments.get('ZYNTHIAN_UI_ONSCREEN_BUTTONS', '0')
		self.request.arguments['ZYNTHIAN_UI_TOUCH_WIDGETS'] = self.request.arguments.get('ZYNTHIAN_UI_TOUCH_WIDGETS', '0')
		self.request.arguments['ZYNTHIAN_VNCSERVER_ENABLED'] = self.request.arguments.get('ZYNTHIAN_VNCSERVER_ENABLED', '0')
		escaped_arguments = tornado.escape.recursive_unicode(self.request.arguments)
		errors = self.update_config(escaped_arguments)

		self.restart_ui_flag = True
		self.get(errors)
