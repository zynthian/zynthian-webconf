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

from zynconf import CustomSwitchActionType, CustomUiAction, ZynSensorActionType
from lib.zynthian_config_handler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# Wiring Configuration
#------------------------------------------------------------------------------


class WiringConfigHandler(ZynthianConfigHandler):

	wiring_presets=OrderedDict([
		["MCP23017_ZynScreen", {
			'ZYNTHIAN_WIRING_ENCODER_A': "102,105,110,113",
			'ZYNTHIAN_WIRING_ENCODER_B': "101,104,109,112",
			'ZYNTHIAN_WIRING_SWITCHES': "100,103,108,111,106,107,114,115",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "2",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "7"
		}],
		["MCP23017_EXTRA", {
			'ZYNTHIAN_WIRING_ENCODER_A': "102,105,110,113",
			'ZYNTHIAN_WIRING_ENCODER_B': "101,104,109,112",
			'ZYNTHIAN_WIRING_SWITCHES': "100,103,108,111,106,107,114,115",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "27",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "25"
		}],
		["MCP23017_ENCODERS", {
			'ZYNTHIAN_WIRING_ENCODER_A': "102,105,110,113",
			'ZYNTHIAN_WIRING_ENCODER_B': "101,104,109,112",
			'ZYNTHIAN_WIRING_SWITCHES': "100,103,108,111",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "27",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "25"
		}],
		["MCP23017_EPDF", {
			'ZYNTHIAN_WIRING_ENCODER_A': "103,100,111,108",
			'ZYNTHIAN_WIRING_ENCODER_B': "104,101,112,109",
			'ZYNTHIAN_WIRING_SWITCHES': "105,102,113,110,106,107,114,115",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "27",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "25"
		}],
		["MCP23017_EPDF_REVERSE", {
			'ZYNTHIAN_WIRING_ENCODER_A': "104,101,112,109",
			'ZYNTHIAN_WIRING_ENCODER_B': "103,100,111,108",
			'ZYNTHIAN_WIRING_SWITCHES': "105,102,113,110,106,107,114,115",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "27",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "25"
		}],
		["PROTOTYPE-5", {
			'ZYNTHIAN_WIRING_ENCODER_A': "26,25,0,4",
			'ZYNTHIAN_WIRING_ENCODER_B': "21,27,7,3",
			'ZYNTHIAN_WIRING_SWITCHES': "107,105,106,104"
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
		["PROTOTYPE-2", {
			'ZYNTHIAN_WIRING_ENCODER_A': "27,21,4,0",
			'ZYNTHIAN_WIRING_ENCODER_B': "25,26,3,7",
			'ZYNTHIAN_WIRING_SWITCHES': "23,107,2,106"
		}],
		["PROTOTYPE-1", {
			'ZYNTHIAN_WIRING_ENCODER_A': "27,21,3,7",
			'ZYNTHIAN_WIRING_ENCODER_B': "25,26,4,0",
			'ZYNTHIAN_WIRING_SWITCHES': "23,None,2,None"
		}],
		["I2C_HWC", {
			'ZYNTHIAN_WIRING_ENCODER_A': "1,2,3,4",
			'ZYNTHIAN_WIRING_ENCODER_B': "0,0,0,0",
			'ZYNTHIAN_WIRING_SWITCHES': "1,2,3,4",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "7",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "0"
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

		config=OrderedDict()

		if os.environ.get('ZYNTHIAN_KIT_VERSION')!='Custom':
			custom_options_disabled = True
			config['ZYNTHIAN_MESSAGE'] = {
				'type': 'html',
				'content': "<div class='alert alert-warning'>Some config options are disabled. You may want to <a href='/hw-kit'>choose Custom Kit</a> for enabling all options.</div>"
			}
		else:
			custom_options_disabled = False

		config['ZYNTHIAN_WIRING_LAYOUT'] = {
			'type': 'select',
			'title': 'Wiring Layout',
			'value': os.environ.get('ZYNTHIAN_WIRING_LAYOUT'),
			'options': list(self.wiring_presets.keys()),
			'presets': self.wiring_presets,
			'disabled': custom_options_disabled
		}
		config['ZYNTHIAN_WIRING_ENCODER_A'] = {
			'type': 'text',
			'title': "Encoders A-pins",
			'value': os.environ.get('ZYNTHIAN_WIRING_ENCODER_A'),
			'advanced': True,
			'disabled': custom_options_disabled
		}
		config['ZYNTHIAN_WIRING_ENCODER_B'] = {
			'type': 'text',
			'title': "Encoders B-pins",
			'value': os.environ.get('ZYNTHIAN_WIRING_ENCODER_B'),
			'advanced': True,
			'disabled': custom_options_disabled
		}
		config['ZYNTHIAN_WIRING_SWITCHES'] = {
			'type': 'text',
			'title': "Switches Pins",
			'value': os.environ.get('ZYNTHIAN_WIRING_SWITCHES'),
			'advanced': True,
			'disabled': custom_options_disabled
		}
		config['ZYNTHIAN_WIRING_MCP23017_INTA_PIN'] = {
			'type': 'select',
			'title': "MCP23017 INT-A Pin",
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
			'advanced': True,
			'disabled': custom_options_disabled
		}
		config['ZYNTHIAN_WIRING_MCP23017_INTB_PIN'] = {
			'type': 'select',
			'title': "MCP23017 INT-B Pin",
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
			'advanced': True,
			'disabled': custom_options_disabled
		}

		zynaptik_config = os.environ.get('ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG',"")
		config['ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG'] = {
			'type': 'select',
			'title': "Zynaptik Config",
			'value': zynaptik_config,
			'options': ["", "16xSWITCH", "4xAD", "16xSWITCH + 4xAD"],
			'advanced': True,
		}

		zyntof_config = os.environ.get('ZYNTHIAN_WIRING_ZYNTOF_CONFIG',"")
		config['ZYNTHIAN_WIRING_ZYNTOF_CONFIG'] = {
			'type': 'select',
			'title': "Num. of Distance Sensors",
			'value': zyntof_config,
			'options': ["", "1", "2", "3", "4"],
			'option_labels': {
				'': '0',
				'1': '1',
				'2': '2',
				'3': '3',
				'4': '4'
			},
			'advanced': True,
		}

		# Customizable Switches
		config['_SECTION_CUSTOM_SWITCHES_'] = {
			'type': 'html',
			'content': "<h3>Customizable Switches</h3>"
		}
		try:
			n_custom_switches = max(0, len(os.environ.get('ZYNTHIAN_WIRING_SWITCHES').split(",")) - 4)
		except:
			n_custom_switches = 0
		for i in range(1, n_custom_switches + 1):
			base_name = 'ZYNTHIAN_WIRING_CUSTOM_SWITCH_{:02d}'.format(i) 
			config[base_name] = {
				'type': 'select',
				'title': 'Switch-{} Action'.format(i),
				'value': os.environ.get(base_name),
				'options': CustomSwitchActionType
			}
			config[base_name + '__UI_SHORT'] = {
				'enabling_options': 'UI_ACTION',
				'type': 'select',
				'title': 'Short-push',
				'value': os.environ.get(base_name + '__UI_SHORT'),
				'options': CustomUiAction
			}
			config[base_name + '__UI_BOLD'] = {
				'enabling_options': 'UI_ACTION',
				'type': 'select',
				'title': 'Bold-push',
				'value': os.environ.get(base_name + '__UI_BOLD'),
				'options': CustomUiAction
			}
			config[base_name + '__UI_LONG'] = {
				'enabling_options': 'UI_ACTION',
				'type': 'select',
				'title': 'Long-push',
				'value': os.environ.get(base_name + '__UI_LONG'),
				'options': CustomUiAction
			}
			config[base_name + '__MIDI_CHAN'] = {
				'enabling_options': 'MIDI_CC MIDI_NOTE MIDI_PROG_CHANGE',
				'type': 'select',
				'title': 'Channel',
				'value': os.environ.get(base_name + '__MIDI_CHAN'),
				'options': ["Active"] + [str(i) for i in range(1,17)]
			}
			config[base_name + '__MIDI_NUM'] = {
				'enabling_options': 'MIDI_CC MIDI_NOTE MIDI_PROG_CHANGE',
				'type': 'select',
				'title': 'Number',
				'value': self.get_custom_midi_num(i),
				'options': [str(i) for i in range(0,128)]
			}

		# Zynaptik ADC input
		if "4xAD" in zynaptik_config:
			config['_SECTION_ZYNAPTIK_AD_'] = {
				'type': 'html',
				'content': "<h3>Zynaptik Analog Input</h3>"
			}
			for i in range(1, 4+1):
				base_name = 'ZYNTHIAN_WIRING_ZYNAPTIK_AD{:02d}'.format(i)
				config[base_name] = {
					'type': 'select',
					'title': 'AD-{} Action'.format(i),
					'value': os.environ.get(base_name),
					'options': ZynSensorActionType
				}
				config[base_name + '__MIDI_CHAN'] = {
					'enabling_options': 'MIDI_CC MIDI_PITCH_BEND MIDI_CHAN_PRESS',
					'type': 'select',
					'title': 'Channel',
					'value': os.environ.get(base_name + '__MIDI_CHAN'),
					'options': ["Active"] + [str(i) for i in range(1,17)]
				}
				config[base_name + '__MIDI_NUM'] = {
					'enabling_options': 'MIDI_CC',
					'type': 'select',
					'title': 'Number',
					'value': self.get_zynaptik_ad_midi_num(i),
					'options': [str(i) for i in range(0,128)]
				}

		# Zyntof input (Distance Sensor)
		if zyntof_config:
			n_zyntofs = int(zyntof_config)
			config['_SECTION_ZYNTOF_'] = {
				'type': 'html',
				'content': "<h3>Distance Sensors</h3>"
			}
			for i in range(1, n_zyntofs+1):
				base_name = 'ZYNTHIAN_WIRING_ZYNTOF{:02d}'.format(i)
				config[base_name] = {
					'type': 'select',
					'title': 'TOF-{} Action'.format(i),
					'value': os.environ.get(base_name),
					'options': ZynSensorActionType
				}
				config[base_name + '__MIDI_CHAN'] = {
					'enabling_options': 'MIDI_CC MIDI_PITCH_BEND MIDI_CHAN_PRESS',
					'type': 'select',
					'title': 'Channel',
					'value': os.environ.get(base_name + '__MIDI_CHAN'),
					'options': ["Active"] + [str(i) for i in range(1,17)]
				}
				config[base_name + '__MIDI_NUM'] = {
					'enabling_options': 'MIDI_CC',
					'type': 'select',
					'title': 'Number',
					'value': self.get_zyntof_midi_num(i),
					'options': [str(i) for i in range(0,128)]
				}

		super().get("Wiring", config, errors)


	def get_custom_midi_num(self, i):
		base_name = "ZYNTHIAN_WIRING_CUSTOM_SWITCH_0{}".format(i)
		v = os.environ.get("{}__MIDI_NUM".format(base_name))
		if v is None:
			v = os.environ.get("{}__CC_NUM".format(base_name),"")
		return v


	def get_zynaptik_ad_midi_num(self, i):
		base_name = "ZYNTHIAN_WIRING_ZYNAPTIK_AD0{}".format(i)
		v = os.environ.get("{}__MIDI_NUM".format(base_name),"")
		return v


	def get_zyntof_midi_num(self, i):
		base_name = "ZYNTHIAN_WIRING_ZYNTOF0{}".format(i)
		v = os.environ.get("{}__MIDI_NUM".format(base_name),"")
		return v


	@tornado.web.authenticated
	def post(self):
		errors=self.update_config(tornado.escape.recursive_unicode(self.request.arguments))
		self.rebuild_zyncoder()
		if not self.reboot_flag:
			self.restart_ui_flag = True
		self.get(errors)


	@classmethod
	def rebuild_zyncoder(cls):
		try:
			cmd="cd %s/zyncoder/build;cmake ..;make" % os.environ.get('ZYNTHIAN_DIR')
			check_output(cmd, shell=True)
		except Exception as e:
			logging.error("Rebuilding Zyncoder Library: %s" % e)

