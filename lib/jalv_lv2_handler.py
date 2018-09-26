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

import os
import logging
import tornado.web
import json
import lilv
from collections import OrderedDict
from lib.zynthian_config_handler import ZynthianConfigHandler


#------------------------------------------------------------------------------
# Jalv LV2 Configuration
#------------------------------------------------------------------------------

class JalvLv2Handler(ZynthianConfigHandler):
	JALV_LV2_CONFIG_FILE = "{}/jalv_plugins.json".format(os.environ.get('ZYNTHIAN_CONFIG_DIR'))
	JALV_ALL_LV2_CONFIG_FILE = "{}/all_jalv_plugins.json".format(os.environ.get('ZYNTHIAN_CONFIG_DIR'))

	all_plugins = None

	@tornado.web.authenticated
	def get(self, errors=None):
		if self.all_plugins is None:
			self.load_all_plugins()

		config=OrderedDict([])
		config['ZYNTHIAN_JALV_PLUGINS'] = self.load_plugins()

		if self.genjson:
			self.write(config)
		else:
			if errors:
				logging.error("Configuring JALV LV2-Plugins  failed: %s" % format(errors))
				self.clear()
				self.set_status(400)
				self.finish("Configuring JALV LV2-Plugins failed: %s" % format(errors))
			else:
				self.render("config.html", body="jalv_lv2.html", config=config, title="JALV Plugins", errors=errors)

	@tornado.web.authenticated
	def post(self):
		action = self.get_argument('ZYNTHIAN_JALV_ACTION')
		if action:
			errors = {
				'ENABLE_PLUGINS': lambda: self.do_enable_plugins(),
				'REGENERATE_PLUGIN_LIST': lambda: self.do_regenerate_plugin_list()
			}[action]()
		self.get(errors)


	def load_all_plugins(self):
		result = OrderedDict()
		trials = 0
		while not result and trials <= 1:
			try:
				trials = trials + 1
				with open(self.JALV_ALL_LV2_CONFIG_FILE) as f:
					result = json.load(f, object_pairs_hook=OrderedDict)
			except Exception as e:
				logging.warning('Loading list of all LV2-Plugins failed: %s' % e)
			if not result:
				self.generate_all_plugins_config_file()
		self.all_plugins = result
		return result


	def generate_all_plugins_config_file(self):
		plugins = OrderedDict()
		try:
			world = lilv.World()
			world.load_all()
			for plugin in world.get_all_plugins():
				logging.info("Adding '{}'".format(plugin.get_name()))
				plugins[str(plugin.get_name())] = {'URL': str(plugin.get_uri()), 'ENABLED': False}
			self.all_plugins = OrderedDict(sorted(plugins.items()))
			with open(self.JALV_ALL_LV2_CONFIG_FILE, 'w') as f:
				json.dump(self.all_plugins, f)

		except Exception as e:
			logging.error('Generating list of all LV2-Plugins failed: %s' % e)


	def load_plugins(self):
		result = self.all_plugins
		enabled_plugins = self.load_enabled_plugins();

		for plugin_name, plugin_properties in result.items():
			if plugin_name in enabled_plugins:
				logging.info("Plugin '{}' enabled".format(plugin_name))
				plugin_properties['ENABLED'] = True

		return result


	def load_enabled_plugins(self):
		result = OrderedDict()
		try:
			with open(self.JALV_LV2_CONFIG_FILE) as f:
				result = json.load(f, object_pairs_hook=OrderedDict)
		except Exception as e:
			logging.info('Loading list of enabled LV2-Plugins failed: %s' % e)
		return result


	def do_enable_plugins(self):
		try:
			pluginJson = OrderedDict()
			self.load_all_plugins()
			postedPlugins = tornado.escape.recursive_unicode(self.request.arguments)

			for plugin_name, plugin_properties in self.all_plugins.items():
				if "ZYNTHIAN_JALV_ENABLE_%s" % plugin_name in postedPlugins:
					pluginJson[plugin_name] = plugin_properties['URL']

			with open(self.JALV_LV2_CONFIG_FILE,'w') as f:
				json.dump(pluginJson, f)

		except Exception as e:
			logging.error("Installing jalv plugins failed: %s" % format(e))
			return format(e)


	def do_regenerate_plugin_list(self):
		self.generate_all_plugins_config_file()
