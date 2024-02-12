# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Engine Manager Handler
#
# Copyright (C) 2018 Markus Heidt <markus@heidt-tech.com>
#
# ********************************************************************
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
# ********************************************************************

import copy
import json
import logging
import tornado.web

from lib.zynthian_config_handler import ZynthianBasicHandler

import zyngine.zynthian_lv2 as zynthian_lv2

# ------------------------------------------------------------------------------
# Engines Info & Configuration
# ------------------------------------------------------------------------------


class EnginesHandler(ZynthianBasicHandler):

	@tornado.web.authenticated
	def get(self, errors=None):
		config = {}
		config['ZYNTHIAN_ENGINES'] = zynthian_lv2.engines_by_type

		# Make a deep copy and remove not serializable objects (ENGINE)
		sengines = copy.deepcopy(zynthian_lv2.engines)
		for key, info in sengines.items():
			try:
				del info['ENGINE']
			except:
				pass
		config['ZYNTHIAN_ENGINES_JSON'] = json.JSONEncoder().encode(sengines)

		try:
			config['ZYNTHIAN_ACTIVE_TAB'] = self.get_argument('ZYNTHIAN_ACTIVE_TAB')
		except:
			pass

		if not 'ZYNTHIAN_ACTIVE_TAB' in config or len(config['ZYNTHIAN_ACTIVE_TAB']) == 0:
			config['ZYNTHIAN_ACTIVE_TAB'] = zynthian_lv2.EngineType.MIDI_SYNTH.value.replace(" ", "_")

		try:
			config['ZYNTHIAN_ENGINES_FILTER'] = self.get_argument('ZYNTHIAN_ENGINES_FILTER')
		except:
			config['ZYNTHIAN_ENGINES_FILTER'] = ''

		if errors:
			logging.error("Configuring engines failed: {}".format(errors))
			self.clear()
			self.set_status(400)
			self.finish("Configuring engines failed: {}".format(errors))
		else:
			super().get("engines.html", "Engines", config, errors)

	@tornado.web.authenticated
	def post(self):
		self.posted_args = tornado.escape.recursive_unicode(self.request.arguments)
		action = self.posted_args['ZYNTHIAN_ENGINES_ACTION'][0]
		logging.debug(f"Executing {action} ...")
		if action == 'ENABLE_ENGINES':
			errors = self.do_enable_engines()
		elif action == "REGENERATE_ENGINES":
			errors = self.do_regenerate_engines()
		elif action == "REGENERATE_LV2_PRESETS_CACHE":
			errors = self.do_regenerate_lv2_presets_cache()
		else:
			errors = {}
		self.get(errors)

	def do_enable_engines(self):
		try:
			for key, info in zynthian_lv2.engines.items():
				if "ZYNTHIAN_ENGINES_ENABLE_{}".format(key) in self.posted_args:
					info['ENABLED'] = True
				else:
					info['ENABLED'] = False
			zynthian_lv2.save_engines()
		except Exception as e:
			logging.error("Enabling engines failed: {}".format(e))
			return format(e)

	def do_regenerate_engines(self):
		prev_engines = zynthian_lv2.engines.keys()
		# Regenerate engine info file, searching for LV2 plugins
		zynthian_lv2.generate_engines_config_file()
		zynthian_lv2.get_engines_by_type()
		# Detect new LV2 plugins and generate presets cache for them
		for key, info in zynthian_lv2.engines.items():
			if key not in prev_engines and 'URL' in info:
				zynthian_lv2.generate_plugin_presets_cache(info['URL'], False)
		# TODO => send CUIA to reload engine info

	def do_regenerate_lv2_presets_cache(self):
		zynthian_lv2.generate_presets_cache_workaround()
		zynthian_lv2.generate_all_presets_cache(False)
		# TODO => send CUIA to reload preset info on running JALV processors

# ------------------------------------------------------------------------------
