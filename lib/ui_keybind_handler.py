# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# UI Keyboard Binding Handler
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

import logging
import tornado.web
from collections import OrderedDict

from lib.zynthian_config_handler import ZynthianBasicHandler
from zyngui import zynthian_gui_keybinding
from zyngui import zynthian_gui
#------------------------------------------------------------------------------
# UI Configuration
#------------------------------------------------------------------------------

class UiKeybindHandler(ZynthianBasicHandler):

	@tornado.web.authenticated
	def get(self, errors=None):
		config = OrderedDict()
		config["map"] = zynthian_gui_keybinding.get_html_map()
		config["cuia_list"] = zynthian_gui.zynthian_gui.get_cuia_list()
		#config["key_map"] = zynthian_gui_keybinding

		super().get("ui_keybind.html", "Keyboard Binding", config, errors)


	@tornado.web.authenticated
	def post(self):
		action = self.get_argument('UI_KEYBINDING_ACTION')
		if action:
			errors = {
				'SAVE': lambda : self.do_save(),
				'RESET': lambda : self.do_reset(),
			}[action]()
		self.get(errors)

	def do_test(self, params=None):
		logging.warning("Test")

	def do_save(self):
		try:
			data = tornado.escape.recursive_unicode(self.request.arguments)
			map = {}
			for key_mod, action in data.items():
				if key_mod == "UI_KEYBINDING_ACTION":
					continue
				try:
					map[key_mod] = action[0].strip()
				except:
					pass
			zynthian_gui_keybinding.set_html_map(map)
			if zynthian_gui_keybinding.save():
				self.reload_key_binding_flag = True
			else:
				return "Failed to save keybindings"

		except Exception as e:
			logging.error("Saving keyboard binding failed: {}".format(e))
			return format(e)


	def do_reset(self):
		try:
			zynthian_gui_keybinding.reset()
			self.reload_key_binding_flag = True

		except Exception as e:
			logging.error("Resetting keyboard binding to defaults failed: {}".format(e))
			return format(e)
	
	
#--------------------------------------------------------------------
