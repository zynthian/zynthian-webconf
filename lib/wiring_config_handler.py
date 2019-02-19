# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Wiring Configuration Handler
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
import tornado.web
import logging
from collections import OrderedDict
from subprocess import check_output
from enum import Enum


from lib.zynthian_config_handler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# Wiring Configuration
#------------------------------------------------------------------------------


class CustomSwitchType(Enum):
	EMPTY = "0"
	POWER_OFF = "1"
	REBOOT = "2"
	ALL_SOUNDS_OFF = "4"
	ALL_NOTES_OFF = "8"
	ALL_OFF = "12"
	UI_RESET = "16"
	ANALOG = "32"

class WiringConfigHandler(ZynthianConfigHandler):

	wiring_presets=OrderedDict([
		["PROTOTYPE-1", {
			'ZYNTHIAN_WIRING_ENCODER_A': "27,21,3,7",
			'ZYNTHIAN_WIRING_ENCODER_B': "25,26,4,0",
			'ZYNTHIAN_WIRING_SWITCHES': "23,None,2,None"
		}],
		["PROTOTYPE-2", {
			'ZYNTHIAN_WIRING_ENCODER_A': "27,21,4,0",
			'ZYNTHIAN_WIRING_ENCODER_B': "25,26,3,7",
			'ZYNTHIAN_WIRING_SWITCHES': "23,107,2,106"
		}],
		["PROTOTYPE-KEES", {
			'ZYNTHIAN_WIRING_ENCODER_A': "27,21,4,5",
			'ZYNTHIAN_WIRING_ENCODER_B': "25,26,31,7",
			'ZYNTHIAN_WIRING_SWITCHES': "23,107,6,106"
		}],
		["PROTOTYPE-3", {
			'ZYNTHIAN_WIRING_ENCODER_A': "27,21,3,7",
			'ZYNTHIAN_WIRING_ENCODER_B': "25,26,4,0",
			'ZYNTHIAN_WIRING_SWITCHES': "107,23,106,2"
		}],
		["PROTOTYPE-3H", {
			'ZYNTHIAN_WIRING_ENCODER_A': "21,27,7,3",
			'ZYNTHIAN_WIRING_ENCODER_B': "26,25,0,4",
			'ZYNTHIAN_WIRING_SWITCHES': "107,23,106,2"
		}],
		["PROTOTYPE-4", {
			'ZYNTHIAN_WIRING_ENCODER_A': "26,25,0,4",
			'ZYNTHIAN_WIRING_ENCODER_B': "21,27,7,3",
			'ZYNTHIAN_WIRING_SWITCHES': "107,23,106,2"
		}],
		["PROTOTYPE-4B", {
			'ZYNTHIAN_WIRING_ENCODER_A': "25,26,4,0",
			'ZYNTHIAN_WIRING_ENCODER_B': "27,21,3,7",
			'ZYNTHIAN_WIRING_SWITCHES': "23,107,2,106"
		}],
		["PROTOTYPE-4-WS32", {
			'ZYNTHIAN_WIRING_ENCODER_A': "26,25,5,4",
			'ZYNTHIAN_WIRING_ENCODER_B': "21,27,7,31",
			'ZYNTHIAN_WIRING_SWITCHES': "107,23,106,6"
		}],
		["PROTOTYPE-5", {
			'ZYNTHIAN_WIRING_ENCODER_A': "26,25,0,4",
			'ZYNTHIAN_WIRING_ENCODER_B': "21,27,7,3",
			'ZYNTHIAN_WIRING_SWITCHES': "107,105,106,104"
		}],
		["MCP23017_ENCODERS", {
			'ZYNTHIAN_WIRING_ENCODER_A': "102,105,110,113",
			'ZYNTHIAN_WIRING_ENCODER_B': "101,104,109,112",
			'ZYNTHIAN_WIRING_SWITCHES': "100,103,108,111",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "27",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "25"
		}],
		["MCP23017_EXTRA", {
			'ZYNTHIAN_WIRING_ENCODER_A': "102,105,110,113",
			'ZYNTHIAN_WIRING_ENCODER_B': "101,104,109,112",
			'ZYNTHIAN_WIRING_SWITCHES': "100,103,108,111,106,107,114,115",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "27",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "25"
		}],
		["EMULATOR", {
			'ZYNTHIAN_WIRING_ENCODER_A': "4,5,6,7",
			'ZYNTHIAN_WIRING_ENCODER_B': "8,9,10,11",
			'ZYNTHIAN_WIRING_SWITCHES': "0,1,2,3"
		}],
		["DUMMIES", {
			'ZYNTHIAN_WIRING_ENCODER_A': "0,0,0,0",
			'ZYNTHIAN_WIRING_ENCODER_B': "0,0,0,0",
			'ZYNTHIAN_WIRING_SWITCHES': "0,0,0,0"
		}],
		["CUSTOM", {
			'ZYNTHIAN_WIRING_ENCODER_A': "",
			'ZYNTHIAN_WIRING_ENCODER_B': "",
			'ZYNTHIAN_WIRING_SWITCHES': ""
		}]
	])

	@tornado.web.authenticated
	def get(self, errors=None):

		custom_type_list = [c.value for c in CustomSwitchType]
		custom_type_labels = dict([(c.value, c.name) for c in CustomSwitchType])

		config=OrderedDict([
			['ZYNTHIAN_WIRING_LAYOUT', {
				'type': 'select',
				'title': 'Wiring Layout',
				'value': os.environ.get('ZYNTHIAN_WIRING_LAYOUT'),
				'options': list(self.wiring_presets.keys()),
				'presets': self.wiring_presets
			}],
			['ZYNTHIAN_WIRING_ENCODER_A', {
				'type': 'text',
				'title': 'Encoders A GPIOs',
				'value': os.environ.get('ZYNTHIAN_WIRING_ENCODER_A'),
				'advanced': True
			}],
			['ZYNTHIAN_WIRING_ENCODER_B', {
				'type': 'text',
				'title': 'Encoders B GPIOs',
				'value': os.environ.get('ZYNTHIAN_WIRING_ENCODER_B'),
				'advanced': True
			}],
			['ZYNTHIAN_WIRING_SWITCHES', {
				'type': 'text',
				'title': 'Switches GPIOs',
				'value': os.environ.get('ZYNTHIAN_WIRING_SWITCHES'),
				'advanced': True
			}],
			['ZYNTHIAN_WIRING_MCP23017_INTA_PIN', {
				'type': 'select',
				'title': 'MPC23017 INTA',
				'value': os.environ.get('ZYNTHIAN_WIRING_MCP23017_INTA_PIN'),
				'options': ['' ,'0', '2', '3', '4', '5', '6', '7', '25', '27'],
				'option_labels': {
					'': 'Default', 
					'0': 'WPi-GPIO 0 (pin 11)',
					'2': 'WPi-GPIO 2 (pin 13)',
					'3': 'WPi-GPIO 3 (pin 15)',
					'4': 'WPi-GPIO 4 (pin 16)',
					'5': 'WPi-GPIO 5 (pin 18)',
					'6': 'WPi-GPIO 6 (pin 22)',
					'7': 'WPi-GPIO 7 (pin 7)',
					'25': 'WPi-GPIO 25 (pin 37)',
					'27': 'WPi-GPIO 27 (pin 36)'
				},
				'advanced': True
			}],
			['ZYNTHIAN_WIRING_MCP23017_INTB_PIN', {
				'type': 'select',
				'title': 'MPC23017 INTB',
				'value': os.environ.get('ZYNTHIAN_WIRING_MCP23017_INTB_PIN'),
				'options': ['' ,'0', '2', '3', '4', '5', '6', '7', '25', '27'],
				'option_labels': {
					'': 'Default', 
					'0': 'WPi-GPIO 0 (pin 11)',
					'2': 'WPi-GPIO 2 (pin 13)',
					'3': 'WPi-GPIO 3 (pin 15)',
					'4': 'WPi-GPIO 4 (pin 16)',
					'5': 'WPi-GPIO 5 (pin 18)',
					'6': 'WPi-GPIO 6 (pin 22)',
					'7': 'WPi-GPIO 7 (pin 7)',
					'25': 'WPi-GPIO 25 (pin 37)',
					'27': 'WPi-GPIO 27 (pin 36)'
				},
				'advanced': True
			}],
			['ZYNTHIAN_WIRING_CUSTOM_SWITCH_A', {
				'type': 'select',
				'title': 'Custom switch A',
				'value': os.environ.get('ZYNTHIAN_WIRING_CUSTOM_SWITCH_A'),
				'options': custom_type_list,
				'option_labels': custom_type_labels,
				'advanced': True
			}],
			['ZYNTHIAN_WIRING_CUSTOM_SWITCH_B', {
				'type': 'select',
				'title': 'Custom switch B',
				'value': os.environ.get('ZYNTHIAN_WIRING_CUSTOM_SWITCH_B'),
				'options': custom_type_list,
				'option_labels': custom_type_labels,
				'advanced': True
			}],
			['ZYNTHIAN_WIRING_CUSTOM_SWITCH_C', {
				'type': 'select',
				'title': 'Custom switch C',
				'value': os.environ.get('ZYNTHIAN_WIRING_CUSTOM_SWITCH_C'),
				'options': custom_type_list,
				'option_labels': custom_type_labels,
				'advanced': True
			}],
			['ZYNTHIAN_WIRING_CUSTOM_SWITCH_D', {
				'type': 'select',
				'title': 'Custom switch D',
				'value': os.environ.get('ZYNTHIAN_WIRING_CUSTOM_SWITCH_D'),
				'options': custom_type_list,
				'option_labels': custom_type_labels,
				'advanced': True
			}]
		])
		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="config_block.html", config=config, title="Wiring", errors=errors)


	@tornado.web.authenticated
	def post(self):
		errors=self.update_config(tornado.escape.recursive_unicode(self.request.arguments))
		self.rebuild_zyncoder()
		self.restart_ui()
		errors=self.get()


	def rebuild_zyncoder(self):
		try:
			cmd="cd %s/zyncoder/build;cmake ..;make" % os.environ.get('ZYNTHIAN_DIR')
			check_output(cmd, shell=True)
		except Exception as e:
			logging.error("Rebuilding Zyncoder Library: %s" % e)

