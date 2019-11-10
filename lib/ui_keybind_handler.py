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
		action = self.get_argument('ZYNTHIAN_KEYBIND_ACTION')
		if action:
			errors = {
				'SAVE_KEYBIND': lambda: self.do_save_keybind(),
			}[action]()
		self.get(errors)

	def do_save_keybind(self):
		try:
			postedBindings = tornado.escape.recursive_unicode(self.request.arguments)

		except Exception as e:
			logging.error("Saving keyboard binding failed: %s" % format(e))
			return format(e)
