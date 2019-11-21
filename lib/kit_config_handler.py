# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Audio Configuration Handler
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
import re
import logging
import tornado.web
from collections import OrderedDict
from subprocess import check_output, call

from lib.zynthian_config_handler import ZynthianConfigHandler
from lib.audio_config_handler import AudioConfigHandler
from lib.display_config_handler import DisplayConfigHandler
from lib.wiring_config_handler import WiringConfigHandler

#------------------------------------------------------------------------------
# Kit Configuration
#------------------------------------------------------------------------------

class KitConfigHandler(ZynthianConfigHandler):

	kit_options = [
		'V3',
		'V2+',
		'V2',
		'V1',
		'Custom'
	]

	@tornado.web.authenticated
	def get(self, errors=None):

		config=OrderedDict([
			['ZYNTHIAN_KIT_VERSION', {
				'type': 'select',
				'title': 'Kit',
				'value': os.environ.get('ZYNTHIAN_KIT_VERSION', 'V2+'),
				'options': self.kit_options
			}]
		])

		super().get("Kit", config, errors)


	@tornado.web.authenticated
	def post(self):
		postedConfig = tornado.escape.recursive_unicode(self.request.arguments)
		current_kit_version = os.environ.get('ZYNTHIAN_KIT_VERSION')

		errors={}
		if postedConfig['ZYNTHIAN_KIT_VERSION'][0]!=current_kit_version:
			errors = self.configure_kit(postedConfig)
			self.reboot_flag = True

		self.get(errors)


	def configure_kit(self, pconfig):
		kit_version = pconfig['ZYNTHIAN_KIT_VERSION'][0]
		if kit_version!="Custom":
			if kit_version=="V3-PRO":
				soundcard_name = "HifiBerry DAC+ ADC PRO"
				display_name = "ZynScreen 3.5 (v1)"
				wiring_layout = "MCP23017_ZynScreen"
			elif kit_version=="V3":
				soundcard_name = "HifiBerry DAC+ ADC"
				display_name = "ZynScreen 3.5 (v1)"
				wiring_layout = "MCP23017_ZynScreen"
			elif kit_version=="V2+":
				soundcard_name = "HifiBerry DAC+ ADC"
				display_name = "PiScreen 3.5 (v2)"
				wiring_layout = "MCP23017_EXTRA"
			elif kit_version=="V2":
				soundcard_name = "HifiBerry DAC+"
				display_name = "PiScreen 3.5 (v2)"
				wiring_layout = "MCP23017_EXTRA"
			elif kit_version=="V1":
				soundcard_name = "HifiBerry DAC+"
				display_name = "PiTFT 2.8 Resistive"
				wiring_layout = "PROTOTYPE-4"

			pconfig['SOUNDCARD_NAME']=[soundcard_name]
			for k,v in AudioConfigHandler.soundcard_presets[soundcard_name].items():
				pconfig[k]=[v]

			pconfig['DISPLAY_NAME']=[display_name]
			for k,v in DisplayConfigHandler.display_presets[display_name].items():
				pconfig[k]=[v]

			pconfig['ZYNTHIAN_WIRING_LAYOUT']=[wiring_layout]
			for k,v in WiringConfigHandler.wiring_presets[wiring_layout].items():
				pconfig[k]=[v]

		errors = self.update_config(pconfig)
		WiringConfigHandler.rebuild_zyncoder()
		
		return errors
