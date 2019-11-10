# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# UI Configuration Handler
#
# Copyright (C) 2019 Brian Walton <brian@riban.co.uk>
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
from zyngui.zynthian_gui_keybinding import zynthian_gui_keybinding

#------------------------------------------------------------------------------
# UI Configuration
#------------------------------------------------------------------------------

class UiKeybindHandler(ZynthianConfigHandler):

	@tornado.web.authenticated
	def get(self, errors=None):
		config=OrderedDict([])
		config['UI_KEYBINDINGS'] = zynthian_gui_keybinding.getInstance().map

		self.render("config.html", body="ui_keybind.html", config=config, title="Keyboard Binding", errors=errors)


	@tornado.web.authenticated
	def post(self):
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
