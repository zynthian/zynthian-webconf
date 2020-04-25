# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Jalv LV2 Plugins Manager Handler
#
# Copyright (C) 2018 Markus Heidt <markus@heidt-tech.com>
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
from lib.zynthian_config_handler import ZynthianConfigHandler

import zyngine.zynthian_lv2 as zynthian_lv2


#------------------------------------------------------------------------------
# Jalv LV2 Configuration
#------------------------------------------------------------------------------

class JalvLv2Handler(ZynthianConfigHandler):

	@tornado.web.authenticated
	def get(self, errors=None):
		config=OrderedDict([])
		config['ZYNTHIAN_JALV_PLUGINS'] = zynthian_lv2.plugins_by_type

		try:
			config['ZYNTHIAN_ACTIVE_TAB'] = self.get_argument('ZYNTHIAN_ACTIVE_TAB')
		except:
			pass

		if not 'ZYNTHIAN_ACTIVE_TAB' in config or len(config['ZYNTHIAN_ACTIVE_TAB']) == 0:
			config['ZYNTHIAN_ACTIVE_TAB'] = zynthian_lv2.PluginType.MIDI_SYNTH.value.replace(" ", "_")

		try:
			config['ZYNTHIAN_JALV_FILTER'] = self.get_argument('ZYNTHIAN_JALV_FILTER')
		except:
			config['ZYNTHIAN_JALV_FILTER'] = ''

		if self.genjson:
			self.write(config)
		else:
			if errors:
				logging.error("Configuring JALV LV2-Plugins  failed: {}".format(errors))
				self.clear()
				self.set_status(400)
				self.finish("Configuring JALV LV2-Plugins failed: {}".format(errors))
			else:
				self.render("config.html", body="jalv_lv2.html", config=config, title="LV2-Plugins", errors=errors)


	@tornado.web.authenticated
	def post(self):
		action = self.get_argument('ZYNTHIAN_JALV_ACTION')
		if action:
			errors = {
				'ENABLE_PLUGINS': lambda: self.do_enable_plugins(),
				'REGENERATE_PLUGIN_LIST': lambda: self.do_regenerate_plugin_list()
			}[action]()
		self.get(errors)


	def do_enable_plugins(self):
		try:
			postedPlugins = tornado.escape.recursive_unicode(self.request.arguments)

			for name, properties in zynthian_lv2.plugins.items():
				if "ZYNTHIAN_JALV_ENABLE_{}".format(name) in postedPlugins:
					zynthian_lv2.plugins[name]['ENABLED'] = True
				else:
					zynthian_lv2.plugins[name]['ENABLED'] = False

			zynthian_lv2.save_plugins()

		except Exception as e:
			logging.error("Enabling jalv plugins failed: {}".format(e))
			return format(e)


	def do_regenerate_plugin_list(self):
		zynthian_lv2.generate_plugins_config_file()
		zynthian_lv2.get_plugins_by_type()

#------------------------------------------------------------------------------
