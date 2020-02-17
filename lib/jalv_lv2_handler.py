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
import time

from collections import OrderedDict
from lib.zynthian_config_handler import ZynthianConfigHandler
from enum import Enum


class PluginType(Enum):
	MIDI_SYNTH = "MIDI Synth"
	MIDI_TOOL = "MIDI Tool"
	AUDIO_EFFECT = "Audio Effect"
	AUDIO_GENERATOR = "Audio Generator"
	#UNKNOWN = "Unknown"


#------------------------------------------------------------------------------
# Jalv LV2 Configuration
#------------------------------------------------------------------------------

class JalvLv2Handler(ZynthianConfigHandler):
	JALV_LV2_CONFIG_FILE = "{}/jalv/plugins.json".format(os.environ.get('ZYNTHIAN_CONFIG_DIR'))
	JALV_LV2_CONFIG_FILE_ALL = "{}/jalv/all_plugins.json".format(os.environ.get('ZYNTHIAN_CONFIG_DIR'))

	plugins = None
	plugin_by_type = None

	world = lilv.World()

	@tornado.web.authenticated
	def get(self, errors=None):
		if self.plugins is None:
			self.load_plugins()

		config=OrderedDict([])
		config['ZYNTHIAN_JALV_PLUGINS'] = self.plugins_by_type

		try:
			config['ZYNTHIAN_ACTIVE_TAB'] = self.get_argument('ZYNTHIAN_ACTIVE_TAB')
		except:
			pass

		if not 'ZYNTHIAN_ACTIVE_TAB' in config or len(config['ZYNTHIAN_ACTIVE_TAB']) == 0:
			config['ZYNTHIAN_ACTIVE_TAB'] = PluginType.MIDI_SYNTH.value.replace(" ", "_")

		try:
			config['ZYNTHIAN_JALV_FILTER'] = self.get_argument('ZYNTHIAN_JALV_FILTER')
		except:
			config['ZYNTHIAN_JALV_FILTER'] = ''

		if self.genjson:
			self.write(config)
		else:
			if errors:
				logging.error("Configuring JALV LV2-Plugins  failed: %s" % format(errors))
				self.clear()
				self.set_status(400)
				self.finish("Configuring JALV LV2-Plugins failed: %s" % format(errors))
			else:
				self.render("config.html", body="jalv_lv2.html", config=config, title="LV2-Plugins", errors=errors)

	@tornado.web.authenticated
	def post(self):
		if self.plugins is None:
			self.load_plugins()

		action = self.get_argument('ZYNTHIAN_JALV_ACTION')
		if action:
			errors = {
				'ENABLE_PLUGINS': lambda: self.do_enable_plugins(),
				'REGENERATE_PLUGIN_LIST': lambda: self.do_regenerate_plugin_list()
			}[action]()
		self.get(errors)


	def load_plugins(self):
		self.convert_from_all_plugins()

		result = OrderedDict()
		try:
			with open(self.JALV_LV2_CONFIG_FILE) as f:
				result = json.load(f, object_pairs_hook=OrderedDict)

			self.plugins = result
			self.get_plugins_by_type()

		except Exception as e:
			logging.warning('Loading list of LV2-Plugins failed: %s' % e)
			self.generate_plugins_config_file()

		return self.plugins


	def generate_plugins_config_file(self):
		plugins = OrderedDict()
		self.world.ns.ev = lilv.Namespace(self.world, 'http://lv2plug.in/ns/ext/event#')

		start = int(round(time.time() * 1000))
		try:
			self.world.load_all()
			for plugin in self.world.get_all_plugins():
				name = str(plugin.get_name())
				logging.info("Adding '{}'".format(name))
				plugins[name] = {'URL': str(plugin.get_uri()), 'TYPE': self.get_plugin_type(plugin).value, 'ENABLED': self.is_plugin_enabled(name)}

			self.plugins = OrderedDict(sorted(plugins.items()))
			self.get_plugins_by_type()

			with open(self.JALV_LV2_CONFIG_FILE, 'w') as f:
				json.dump(self.plugins, f)

		except Exception as e:
			logging.error('Generating list of LV2-Plugins failed: %s' % e)

		end = int(round(time.time() * 1000))
		logging.info('LV2 plugin list generation took {}s'.format(end-start))


	def get_plugins_by_type(self):
		self.plugins_by_type = OrderedDict()
		for t in PluginType:
			self.plugins_by_type[t.value] = OrderedDict()

		for name, properties in self.plugins.items():
			self.plugins_by_type[properties['TYPE']][name] = properties

		return self.plugins_by_type


	def do_enable_plugins(self):
		try:
			self.load_plugins()
			postedPlugins = tornado.escape.recursive_unicode(self.request.arguments)

			for name, properties in self.plugins.items():
				if "ZYNTHIAN_JALV_ENABLE_%s" % name in postedPlugins:
					self.plugins[name]['ENABLED'] = True
				else:
					self.plugins[name]['ENABLED'] = False

			with open(self.JALV_LV2_CONFIG_FILE,'w') as f:
				json.dump(self.plugins, f)

		except Exception as e:
			logging.error("Enabling jalv plugins failed: %s" % format(e))
			return format(e)


	def do_regenerate_plugin_list(self):
		self.generate_plugins_config_file()


	def convert_from_all_plugins(self):
		try:
			with open(self.JALV_LV2_CONFIG_FILE_ALL) as f:
				plugins = json.load(f, object_pairs_hook=OrderedDict)

			with open(self.JALV_LV2_CONFIG_FILE) as f:
				enplugins = json.load(f, object_pairs_hook=OrderedDict)

			logging.info("Converting LV2 config files ...")

			for name, properties in plugins.items():
				if name in enplugins:
					plugins[name]['ENABLED'] = True
				else:
					plugins[name]['ENABLED'] = False

			with open(self.JALV_LV2_CONFIG_FILE,'w') as f:
				json.dump(plugins, f)

			os.remove(self.JALV_LV2_CONFIG_FILE_ALL)

		except Exception as e:
			#logging.error(e)
			pass


	def is_plugin_enabled(self, plugin_name):
		try:
			return self.plugins[plugin_name]['ENABLED']
		except:
			return False


	def get_plugin_type(self, pl):
		lv2_plugin_classes = {
			"MIDI_SYNTH" : ("Instrument"),

			"AUDIO_EFFECT" : ("Analyser", "Spectral", "Delay", "Compressor", "Distortion", "Filter", "Equaliser",
				"Modulator", "Expander", "Spatial", "Limiter", "Pitch Shifter", "Reverb", "Simulator", "Envelope",
				"Gate", "Amplifier", "Chorus", "Flanger", "Phaser", "Highpass", "Lowpass", "Dynamics"),

			"AUDIO_GENERATOR": ("Oscillator", "Generator"),

			"UNKNOWN": ("Utility", "Plugin")
		}

		# Try to determine the plugin type from the LV2 class ...
		plugin_class = str(pl.get_class().get_label())
		if plugin_class in lv2_plugin_classes["MIDI_SYNTH"]:
			return PluginType.MIDI_SYNTH

		elif plugin_class in lv2_plugin_classes["AUDIO_EFFECT"]:
			return PluginType.AUDIO_EFFECT

		elif plugin_class in lv2_plugin_classes["AUDIO_GENERATOR"]:
			return PluginType.AUDIO_GENERATOR

		# If failed to determine the plugin type using the LV2 class, 
		# inspect the input/output ports ...

		n_audio_in = pl.get_num_ports_of_class(self.world.ns.lv2.InputPort,  self.world.ns.lv2.AudioPort)
		n_audio_out = pl.get_num_ports_of_class(self.world.ns.lv2.OutputPort, self.world.ns.lv2.AudioPort)
		n_midi_in = pl.get_num_ports_of_class(self.world.ns.lv2.InputPort,  self.world.ns.ev.EventPort)
		n_midi_out = pl.get_num_ports_of_class(self.world.ns.lv2.OutputPort, self.world.ns.ev.EventPort)
		n_midi_in += pl.get_num_ports_of_class(self.world.ns.lv2.InputPort,  self.world.ns.atom.AtomPort)
		n_midi_out += pl.get_num_ports_of_class(self.world.ns.lv2.OutputPort, self.world.ns.atom.AtomPort)

		# Really DIRTY => Should be fixed ASAP!!! TODO!!
		#plugin_name=str(pl.get_name())
		#if plugin_name[-2:]=="v1":
		#	return PluginType.MIDI_SYNTH

		#if plugin_name[:2]=="EQ":
		#	return PluginType.AUDIO_EFFECT

		if n_audio_out>0 and n_audio_in==0:
			if n_midi_in>0:
				return PluginType.MIDI_SYNTH
			else:
				return PluginType.AUDIO_GENERATOR

		if n_audio_out>0 and n_audio_in>0 and n_midi_out==0:
			return PluginType.AUDIO_EFFECT

		if n_midi_in>0 and n_midi_out>0 and n_audio_in==n_audio_out==0:
			return PluginType.MIDI_TOOL

		#return PluginType.UNKNOWN
		return PluginType.AUDIO_EFFECT


