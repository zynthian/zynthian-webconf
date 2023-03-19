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
from zyngui.zynthian_gui_keybinding import zynthian_gui_keybinding
from zyngui.zynthian_gui import zynthian_gui

#------------------------------------------------------------------------------
# UI Configuration
#------------------------------------------------------------------------------

class UiKeybindHandler(ZynthianBasicHandler):

	@tornado.web.authenticated
	def get(self, errors=None):
		config = OrderedDict()
		config["map"] = zynthian_gui_keybinding.map
		config["cuia_list"] = zynthian_gui.get_cuia_list()
		config["keymap"] = zynthian_gui_keybinding.get_keymap()

		super().get("ui_keybind.html", "Keyboard Binding", config, errors)


	@tornado.web.authenticated
	def post(self):
		action = self.get_argument('UI_KEYBINDING_ACTION')
		if action:
			if action.startswith('REMOVE '):
				action, params = action.split(" ", 1)
			else:
				params = None
			errors = {
				'SAVE': lambda p: self.do_save(p),
				'RESET': lambda p: self.do_reset(p),
				'REMOVE' : lambda p: self.do_remove(p)
			}[action](params)
		self.get(errors)

	def do_test(self, params=None):
		logging.warning("Test")

	def do_remove(self, param):
		try:
			zynthian_gui_keybinding.remove_binding(param)
			self.reload_key_binding_flag = False
		except Exception as e:
			logging.error("Removing keyboard binding failed: {}".format(e))
			return format(e)


	def do_save(self, params):
		try:
			data = tornado.escape.recursive_unicode(self.request.arguments)
			zynthian_gui_keybinding.map = {}
			for x, val in data.items():
				try:
					val = val[0]
					key, param = x.split(":")
					if key in zynthian_gui_keybinding.map:
						if param == "action":
							zynthian_gui_keybinding.map[key] = f"{val} {zynthian_gui_keybinding.map[key]}".strip()
						elif param == "params":
							zynthian_gui_keybinding.map[key] = f"{zynthian_gui_keybinding.map[key]} {val}".strip()
					else:
						zynthian_gui_keybinding.map[key] = val
				except:
					pass
			if zynthian_gui_keybinding.save():
				self.reload_key_binding_flag = True
			else:
				return "Failed to save keybindings"

		except Exception as e:
			logging.error("Saving keyboard binding failed: {}".format(e))
			return format(e)


	def do_reset(self, params):
		try:
			zynthian_gui_keybinding.reset_config()
			#zynthian_gui_keybinding.save()
			self.reload_key_binding_flag = True

		except Exception as e:
			logging.error("Resetting keyboard binding to defaults failed: {}".format(e))
			return format(e)
	
	
#--------------------------------------------------------------------
