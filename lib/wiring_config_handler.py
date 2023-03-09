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
import re
import logging
import tornado.web
from enum import Enum
from subprocess import check_output
from collections import OrderedDict

from zynconf import CustomSwitchActionType, ZynSensorActionType
from lib.zynthian_config_handler import ZynthianConfigHandler
from lib.dashboard_handler import DashboardHandler
from zyngui.zynthian_gui import zynthian_gui


#------------------------------------------------------------------------------
# Autodetect I2C chips
#------------------------------------------------------------------------------

ADS1115_I2C_ADDRESS = ""
MCP4728_I2C_ADDRESS = ""

for i2chip in DashboardHandler.get_i2c_chips():
	parts = i2chip.split('@')
	if parts[0] == 'ADS1115':
		ADS1115_I2C_ADDRESS = parts[1]
	elif parts[0] == 'MCP4728':
		MCP4728_I2C_ADDRESS = parts[1]

#------------------------------------------------------------------------------
# Wiring Configuration
#------------------------------------------------------------------------------

class WiringConfigHandler(ZynthianConfigHandler):
	PROFILES_DIRECTORY = "{}/wiring-profiles".format(os.environ.get("ZYNTHIAN_CONFIG_DIR"))

	wiring_presets = OrderedDict([
		["V5", {
			'ZYNTHIAN_WIRING_ENCODER_A': "",
			'ZYNTHIAN_WIRING_ENCODER_B': "",
			'ZYNTHIAN_WIRING_SWITCHES': "",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': "",
			'ZYNTHIAN_WIRING_LAYOUT_CUSTOM_PROFILE': 'v5'
		}],
		["Z2_V3", {
			'ZYNTHIAN_WIRING_ENCODER_A': "",
			'ZYNTHIAN_WIRING_ENCODER_B': "",
			'ZYNTHIAN_WIRING_SWITCHES': "",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': "",
			'ZYNTHIAN_WIRING_LAYOUT_CUSTOM_PROFILE': 'z2'
		}],
		["Z2_V2", {
			'ZYNTHIAN_WIRING_ENCODER_A': "",
			'ZYNTHIAN_WIRING_ENCODER_B': "",
			'ZYNTHIAN_WIRING_SWITCHES': "",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': "",
			'ZYNTHIAN_WIRING_LAYOUT_CUSTOM_PROFILE': 'z2'
		}],
		["Z2_V1", {
			'ZYNTHIAN_WIRING_ENCODER_A': "",
			'ZYNTHIAN_WIRING_ENCODER_B': "",
			'ZYNTHIAN_WIRING_SWITCHES': "",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': "",
			'ZYNTHIAN_WIRING_LAYOUT_CUSTOM_PROFILE': 'z2'
		}],
		["MCP23017_Zynaptik-3_Zynface", {
			'ZYNTHIAN_WIRING_ENCODER_A': "102,105,110,113",
			'ZYNTHIAN_WIRING_ENCODER_B': "101,104,109,112",
			'ZYNTHIAN_WIRING_SWITCHES': "100,103,108,111,106,107,114,115",
			'ZYNTHIAN_WIRING_MCP23017_I2C_ADDRESS': "0x21",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "27",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "25",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "Zynaptik-3 (4xAD + 4xDA)",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': ADS1115_I2C_ADDRESS,
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': MCP4728_I2C_ADDRESS,
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': "2",
			'ZYNTHIAN_WIRING_LAYOUT_CUSTOM_PROFILE': 'v4_studio'
		}],
		["MCP23017_Zynaptik-3", {
			'ZYNTHIAN_WIRING_ENCODER_A': "102,105,110,113",
			'ZYNTHIAN_WIRING_ENCODER_B': "101,104,109,112",
			'ZYNTHIAN_WIRING_SWITCHES': "100,103,108,111,106,107,114,115",
			'ZYNTHIAN_WIRING_MCP23017_I2C_ADDRESS': "0x21",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "27",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "25",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "Zynaptik-3 (4xAD + 4xDA)",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': ADS1115_I2C_ADDRESS,
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': MCP4728_I2C_ADDRESS,
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': "",
			'ZYNTHIAN_WIRING_LAYOUT_CUSTOM_PROFILE': 'v4_studio'
		}],
		["MCP23017_ZynScreen_Zynface", {
			'ZYNTHIAN_WIRING_ENCODER_A': "102,105,110,113",
			'ZYNTHIAN_WIRING_ENCODER_B': "101,104,109,112",
			'ZYNTHIAN_WIRING_SWITCHES': "100,103,108,111,106,107,114,115",
			'ZYNTHIAN_WIRING_MCP23017_I2C_ADDRESS': "0x20",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "2",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "7",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "Zynaptik-2 (16xDIO + 4xAD + 4xDA)",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': ADS1115_I2C_ADDRESS,
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': MCP4728_I2C_ADDRESS,
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': "2",
			'ZYNTHIAN_WIRING_LAYOUT_CUSTOM_PROFILE': 'v4_studio'
		}],
		["MCP23017_ZynScreen_Zynaptik", {
			'ZYNTHIAN_WIRING_ENCODER_A': "102,105,110,113",
			'ZYNTHIAN_WIRING_ENCODER_B': "101,104,109,112",
			'ZYNTHIAN_WIRING_SWITCHES': "100,103,108,111,106,107,114,115",
			'ZYNTHIAN_WIRING_MCP23017_I2C_ADDRESS': "0x20",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "2",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "7",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "Zynaptik-2 (16xDIO + 4xAD + 4xDA)",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': ADS1115_I2C_ADDRESS,
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': MCP4728_I2C_ADDRESS,
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': "",
			'ZYNTHIAN_WIRING_LAYOUT_CUSTOM_PROFILE': 'v4_studio'
		}],
		["MCP23017_ZynScreen", {
			'ZYNTHIAN_WIRING_ENCODER_A': "102,105,110,113",
			'ZYNTHIAN_WIRING_ENCODER_B': "101,104,109,112",
			'ZYNTHIAN_WIRING_SWITCHES': "100,103,108,111,106,107,114,115",
			'ZYNTHIAN_WIRING_MCP23017_I2C_ADDRESS': "0x20",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "2",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "7",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': "",
			'ZYNTHIAN_WIRING_LAYOUT_CUSTOM_PROFILE': 'v4_studio'
		}],
		["MCP23017_EXTRA", {
			'ZYNTHIAN_WIRING_ENCODER_A': "102,105,110,113",
			'ZYNTHIAN_WIRING_ENCODER_B': "101,104,109,112",
			'ZYNTHIAN_WIRING_SWITCHES': "100,103,108,111,106,107,114,115",
			'ZYNTHIAN_WIRING_MCP23017_I2C_ADDRESS': "0x20",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "27",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "25",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': "",
			'ZYNTHIAN_WIRING_LAYOUT_CUSTOM_PROFILE': 'v4_studio'
		}],
		["MCP23017_ENCODERS", {
			'ZYNTHIAN_WIRING_ENCODER_A': "102,105,110,113",
			'ZYNTHIAN_WIRING_ENCODER_B': "101,104,109,112",
			'ZYNTHIAN_WIRING_SWITCHES': "100,103,108,111",
			'ZYNTHIAN_WIRING_MCP23017_I2C_ADDRESS': "0x20",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "27",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "25",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': ""
		}],
		["MCP23017_EPDF", {
			'ZYNTHIAN_WIRING_ENCODER_A': "103,100,111,108",
			'ZYNTHIAN_WIRING_ENCODER_B': "104,101,112,109",
			'ZYNTHIAN_WIRING_SWITCHES': "105,102,113,110,106,107,114,115",
			'ZYNTHIAN_WIRING_MCP23017_I2C_ADDRESS': "0x20",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "27",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "25",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': ""
		}],
		["MCP23017_EPDF_REVERSE", {
			'ZYNTHIAN_WIRING_ENCODER_A': "104,101,112,109",
			'ZYNTHIAN_WIRING_ENCODER_B': "103,100,111,108",
			'ZYNTHIAN_WIRING_SWITCHES': "105,102,113,110,106,107,114,115",
			'ZYNTHIAN_WIRING_MCP23017_I2C_ADDRESS': "0x20",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "27",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "25",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': ""
		}],
		["PROTOTYPE-5", {
			'ZYNTHIAN_WIRING_ENCODER_A': "26,25,0,4",
			'ZYNTHIAN_WIRING_ENCODER_B': "21,27,7,3",
			'ZYNTHIAN_WIRING_SWITCHES': "107,105,106,104",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': ""
		}],
		["PROTOTYPE-4", {
			'ZYNTHIAN_WIRING_ENCODER_A': "26,25,0,4",
			'ZYNTHIAN_WIRING_ENCODER_B': "21,27,7,3",
			'ZYNTHIAN_WIRING_SWITCHES': "107,23,106,2",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': ""
		}],
		["PROTOTYPE-4B", {
			'ZYNTHIAN_WIRING_ENCODER_A': "25,26,4,0",
			'ZYNTHIAN_WIRING_ENCODER_B': "27,21,3,7",
			'ZYNTHIAN_WIRING_SWITCHES': "23,107,2,106",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': ""
		}],
		["PROTOTYPE-4-WS32", {
			'ZYNTHIAN_WIRING_ENCODER_A': "26,25,5,4",
			'ZYNTHIAN_WIRING_ENCODER_B': "21,27,7,31",
			'ZYNTHIAN_WIRING_SWITCHES': "107,23,106,6",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': ""
		}],
		["PROTOTYPE-3", {
			'ZYNTHIAN_WIRING_ENCODER_A': "27,21,3,7",
			'ZYNTHIAN_WIRING_ENCODER_B': "25,26,4,0",
			'ZYNTHIAN_WIRING_SWITCHES': "107,23,106,2",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': ""
		}],
		["PROTOTYPE-3H", {
			'ZYNTHIAN_WIRING_ENCODER_A': "21,27,7,3",
			'ZYNTHIAN_WIRING_ENCODER_B': "26,25,0,4",
			'ZYNTHIAN_WIRING_SWITCHES': "107,23,106,2",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': ""
		}],
		["PROTOTYPE-2", {
			'ZYNTHIAN_WIRING_ENCODER_A': "27,21,4,0",
			'ZYNTHIAN_WIRING_ENCODER_B': "25,26,3,7",
			'ZYNTHIAN_WIRING_SWITCHES': "23,107,2,106",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': ""
		}],
		["PROTOTYPE-1", {
			'ZYNTHIAN_WIRING_ENCODER_A': "27,21,3,7",
			'ZYNTHIAN_WIRING_ENCODER_B': "25,26,4,0",
			'ZYNTHIAN_WIRING_SWITCHES': "23,None,2,None",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': ""
		}],
		["I2C_HWC", {
			'ZYNTHIAN_WIRING_ENCODER_A': "1,2,3,4",
			'ZYNTHIAN_WIRING_ENCODER_B': "0,0,0,0",
			'ZYNTHIAN_WIRING_SWITCHES': "1,2,3,4",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "7",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "0",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': ""
		}],
		["EMULATOR", {
			'ZYNTHIAN_WIRING_ENCODER_A': "4,5,6,7",
			'ZYNTHIAN_WIRING_ENCODER_B': "8,9,10,11",
			'ZYNTHIAN_WIRING_SWITCHES': "0,1,2,3",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': ""
		}],
		["DUMMIES", {
			'ZYNTHIAN_WIRING_ENCODER_A': "0,0,0,0",
			'ZYNTHIAN_WIRING_ENCODER_B': "0,0,0,0",
			'ZYNTHIAN_WIRING_SWITCHES': "0,0,0,0",
			'ZYNTHIAN_WIRING_MCP23017_INTA_PIN': "",
			'ZYNTHIAN_WIRING_MCP23017_INTB_PIN': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': "",
			'ZYNTHIAN_WIRING_ZYNTOF_CONFIG': ""
		}],
		["CUSTOM", {
			'ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS': ADS1115_I2C_ADDRESS,
			'ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS': MCP4728_I2C_ADDRESS
		}]
	])

	def get_cuia(self, envar):
		v = os.environ.get(envar, "")
		try:
			parts = v.split(" ", 2)
			cuia_name = parts[0]
			try:
				cuia_param = parts[1]
			except:
				cuia_param = ""
		except:
			cuia_name = ""
			cuia_param = ""
		return cuia_name, cuia_param

	def prepare(self):
		super().prepare()
		self.current_custom_profile = os.environ.get('ZYNTHIAN_WIRING_LAYOUT_CUSTOM_PROFILE',"")
		self.load_custom_profiles()


	@tornado.web.authenticated
	def get(self, errors=None):
		config = OrderedDict()

		if os.environ.get('ZYNTHIAN_KIT_VERSION') != 'Custom':
			custom_options_disabled = True
			config['ZYNTHIAN_MESSAGE'] = {
				'type': 'html',
				'content': "<div class='alert alert-warning'>Some config options are disabled. You may want to <a href='/hw-kit'>choose Custom Kit</a> for enabling all options.</div>"
			}
		else:
			custom_options_disabled = False

		wiring_layout = os.environ.get('ZYNTHIAN_WIRING_LAYOUT',"")
		wiring_switches = os.environ.get('ZYNTHIAN_WIRING_SWITCHES',"")
		zynaptik_config = os.environ.get('ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG',"")
		zyntof_config = os.environ.get('ZYNTHIAN_WIRING_ZYNTOF_CONFIG',"")

		config['ZYNTHIAN_WIRING_LAYOUT'] = {
			'type': 'select',
			'title': 'Wiring Layout',
			'value': wiring_layout,
			'options': list(self.wiring_presets.keys()),
			'presets': self.wiring_presets,
			'disabled': custom_options_disabled,
			'refresh_on_change': True,
			'div_class': "col-sm-12"
		}

		if wiring_layout.startswith("Z2"):
			encoders_config_flag = False
			n_extra_switches = 32
		elif wiring_layout.startswith("V5"):
			encoders_config_flag = False
			n_extra_switches = 24
		else:
			encoders_config_flag = True
			try:
				# Calculate Num of Custom Switches
				n_extra_switches = min(4,max(0, len(wiring_switches.split(",")) - 4))
			except:
				n_extra_switches = 0

		if encoders_config_flag:
			config['ZYNTHIAN_WIRING_ENCODER_A'] = {
				'type': 'text',
				'title': "Encoders A-pins",
				'value': os.environ.get('ZYNTHIAN_WIRING_ENCODER_A'),
				'advanced': True,
				'disabled': custom_options_disabled,
				'div_class': "col-sm-4"
			}
			config['ZYNTHIAN_WIRING_ENCODER_B'] = {
				'type': 'text',
				'title': "Encoders B-pins",
				'value': os.environ.get('ZYNTHIAN_WIRING_ENCODER_B'),
				'advanced': True,
				'disabled': custom_options_disabled,
				'div_class': "col-sm-4"
			}
			config['ZYNTHIAN_WIRING_SWITCHES'] = {
				'type': 'text',
				'title': "Switches Pins",
				'value': wiring_switches,
				'advanced': True,
				'disabled': custom_options_disabled,
				'div_class': "col-sm-4"
			}
		else:
			config['ZYNTHIAN_WIRING_ENCODER_A'] = {
				'type': 'hidden',
				'value': os.environ.get('ZYNTHIAN_WIRING_ENCODER_A')
			}
			config['ZYNTHIAN_WIRING_ENCODER_B'] = {
				'type': 'hidden',
				'value': os.environ.get('ZYNTHIAN_WIRING_ENCODER_B')
			}
			config['ZYNTHIAN_WIRING_SWITCHES'] = {
				'type': 'hidden',
				'value': os.environ.get('ZYNTHIAN_WIRING_SWITCHES')
			}

		if wiring_layout.startswith("MCP23017") or wiring_layout == "CUSTOM":
			config['ZYNTHIAN_WIRING_MCP23017_I2C_ADDRESS'] = {
				'type': 'select',
				'title': "MCP23017 I2C Address",
				'value': os.environ.get('ZYNTHIAN_WIRING_MCP23017_I2C_ADDRESS'),
				'options': ['' ,'0x20', '0x21', '0x22', '0x23', '0x24', '0x25', '0x26', '0x27'],
				'advanced': True,
				'disabled': custom_options_disabled,
				'div_class': "col-sm-4"
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
				'disabled': custom_options_disabled,
				'div_class': "col-sm-4"
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
				'disabled': custom_options_disabled,
				'div_class': "col-sm-4"
			}
			config['ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG'] = {
				'type': 'select',
				'title': "Zynaptik Config",
				'value': zynaptik_config,
				'options': ["", "Custom 16xDIO", "Custom 4xAD", "Custom 4xDA", "Custom 16xDIO + 4xAD", "Custom 16xDIO + 4xDA", "Custom 4xAD + 4xDA", "Custom 16xDIO + 4xAD + 4xDA", "Zynaptik-2 (16xDIO + 4xAD + 4xDA)", "Zynaptik-3 (16xDIO + 4xAD + 4xDA)", "Zynaptik-3 (4xAD + 4xDA)"],
				'advanced': True,
				'refresh_on_change': True,
				'div_class': "col-sm-4"
			}
			config['ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS'] = {
				'type': 'select',
				'title': "ADS1115 I2C Address",
				'value': os.environ.get('ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS'),
				'options': ['' ,'0x48', '0x49', '0x4A', '0x4B'],
				'advanced': True,
				'disabled': custom_options_disabled,
				'div_class': "col-sm-4"
			}
			config['ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS'] = {
				'type': 'select',
				'title': "MCP4728 I2C Address",
				'value': os.environ.get('ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS'),
				'options': ['' ,'0x60', '0x61', '0x62', '0x63', '0x64', '0x65', '0x66', '0x67'],
				'advanced': True,
				'disabled': custom_options_disabled,
				'div_class': "col-sm-4"
			}
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
				'refresh_on_change': True
			}
		elif wiring_layout.startswith("I2C"):
			config['ZYNTHIAN_WIRING_MCP23017_I2C_ADDRESS'] = {
				'type': 'hidden',
				'value': os.environ.get('ZYNTHIAN_WIRING_MCP23017_I2C_ADDRESS')
			}
			config['ZYNTHIAN_WIRING_MCP23017_INTA_PIN'] = {
				'type': 'select',
				'title': "INT Pin",
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
				'type': 'hidden',
				'value': os.environ.get('ZYNTHIAN_WIRING_MCP23017_INTB_PIN')
			}
			config['ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG'] = {
				'type': 'hidden',
				'value': zynaptik_config
			}
			config['ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS'] = {
				'type': 'hidden',
				'value': os.environ.get('ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS')
			}
			config['ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS'] = {
				'type': 'hidden',
				'value': os.environ.get('ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS')
			}
			config['ZYNTHIAN_WIRING_ZYNTOF_CONFIG'] = {
				'type': 'hidden',
				'value': zyntof_config
			}
		else:
			config['ZYNTHIAN_WIRING_MCP23017_I2C_ADDRESS'] = {
				'type': 'hidden',
				'value': os.environ.get('ZYNTHIAN_WIRING_MCP23017_I2C_ADDRESS')
			}
			config['ZYNTHIAN_WIRING_MCP23017_INTA_PIN'] = {
				'type': 'hidden',
				'value': os.environ.get('ZYNTHIAN_WIRING_MCP23017_INTA_PIN')
			}
			config['ZYNTHIAN_WIRING_MCP23017_INTB_PIN'] = {
				'type': 'hidden',
				'value': os.environ.get('ZYNTHIAN_WIRING_MCP23017_INTB_PIN')
			}
			config['ZYNTHIAN_WIRING_ZYNAPTIK_CONFIG'] = {
				'type': 'hidden',
				'value': zynaptik_config
			}
			config['ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS'] = {
				'type': 'hidden',
				'value': os.environ.get('ZYNTHIAN_WIRING_ZYNAPTIK_ADS1115_I2C_ADDRESS')
			}
			config['ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS'] = {
				'type': 'hidden',
				'value': os.environ.get('ZYNTHIAN_WIRING_ZYNAPTIK_MCP4728_I2C_ADDRESS')
			}
			config['ZYNTHIAN_WIRING_ZYNTOF_CONFIG'] = {
				'type': 'hidden',
				'value': zyntof_config
			}

		if "16xDIO" in zynaptik_config:
			n_zynaptik_switches = 16
		else:
			n_zynaptik_switches = 0

		# Wiring Layout Profiles
		config['ZYNTHIAN_WIRING_LAYOUT_CUSTOM_PROFILE'] = {
			'type': 'select',
			'title': 'Customization Profile',
			'value': self.current_custom_profile,
			'options': self.custom_profiles.keys(),
			'presets': self.custom_profiles,
			'refresh_on_change': True,
			'div_class': "col-sm-8 col-xs-12"
		}
		config['zynthian_wiring_layout_saveas_script'] = {
			'type': 'button',
			'title': 'Save as ...',
			'button_type': 'button',
			'class': 'btn-theme btn-block',
			'icon' : 'fa fa-plus',
			'script_file': 'wiring_layout_saveas.js',
			'div_class': "col-sm-2 col-xs-6",
			'inline': 1
		}
		config['zynthian_wiring_layout_delete_script'] = {
			'type': 'button',
			'title': 'Delete',
			'button_type': 'submit',
			'class': 'btn-danger btn-block',
			'icon' : 'fa fa-trash-o',
			'script_file': 'wiring_layout_delete.js',
			'div_class': "col-sm-2 col-xs-6",
			'inline': 1
		}
		config['zynthian_wiring_layout_saveas_fname'] = {
			'type': 'hidden',
			'value': ''
		}

		div_class = "col-sm-3 col-xs-12 col-fixheight"
		div_class1 = "col-sm-3 col-xs-12 col-fixheight col-thin-padding"
		div_class2 = "col-sm-2 col-xs-9 col-fixheight col-thin-padding-extra"
		div_class2x = "col-sm-1 col-xs-3 col-fixheight col-extra"

		# Customizable Switches
		self.n_custom_switches = n_extra_switches + n_zynaptik_switches

		cuia_list = [""] + zynthian_gui.get_cuia_list()
		cvgate_in = []
		cvgate_out = []
		if self.n_custom_switches > 0:
			config['_SECTION_CUSTOM_SWITCHES_'] = {
				'type': 'html',
				'content': "<h3>Customizable Switches</h3>",
				'advanced': True
			}
			for i in range(self.n_custom_switches):
				base_name = 'ZYNTHIAN_WIRING_CUSTOM_SWITCH_{:02d}'.format(i+1)

				if i < n_extra_switches:
					title = 'Switch-{} Action'.format(i+1)
				else:
					title = 'Zynaptik Switch-{} Action'.format(i+1-n_extra_switches)

				action_type = os.environ.get(base_name, "NONE")
				cvchan = int(os.environ.get(base_name + '__CV_CHAN', 1))
				if action_type == "UI_ACTION":
					action_type = "UI_ACTION_RELEASE"
				elif action_type == "CVGATE_IN":
					cvgate_in.append(cvchan)
				elif action_type == "CVGATE_OUT":
					cvgate_out.append(cvchan)

				config[base_name] = {
					'type': 'select',
					'title': title,
					'value': action_type,
					'options': CustomSwitchActionType,
					'refresh_on_change': True,
					'div_class': div_class,
					'advanced': True
				}
				cuia_name, cuia_param = self.get_cuia(base_name + '__UI_PUSH')
				config[base_name + '__UI_PUSH__CUIA_NAME'] = {
					'enabling_options': 'UI_ACTION_PUSH',
					'type': 'select',
					'title': 'Push',
					'value': cuia_name,
					'options': cuia_list,
					'div_class': div_class2,
					'advanced': True
				}
				config[base_name + '__UI_PUSH__CUIA_PARAM'] = {
					'enabling_options': 'UI_ACTION_PUSH',
					'type': 'text',
					'title': '',
					'value': cuia_param,
					'div_class': div_class2x,
					'advanced': True
				}
				cuia_name, cuia_param = self.get_cuia(base_name + '__UI_SHORT')
				config[base_name + '__UI_SHORT__CUIA_NAME'] = {
					'enabling_options': 'UI_ACTION_RELEASE',
					'type': 'select',
					'title': 'Short-push',
					'value': cuia_name,
					'options': cuia_list,
					'div_class': div_class2,
					'advanced': True
				}
				config[base_name + '__UI_SHORT__CUIA_PARAM'] = {
					'enabling_options': 'UI_ACTION_RELEASE',
					'type': 'text',
					'title': '',
					'value': cuia_param,
					'div_class': div_class2x,
					'advanced': True
				}
				cuia_name, cuia_param = self.get_cuia(base_name + '__UI_BOLD')
				config[base_name + '__UI_BOLD__CUIA_NAME'] = {
					'enabling_options': 'UI_ACTION_RELEASE',
					'type': 'select',
					'title': 'Bold-push',
					'value': cuia_name,
					'options': cuia_list,
					'div_class': div_class2,
					'advanced': True
				}
				config[base_name + '__UI_BOLD__CUIA_PARAM'] = {
					'enabling_options': 'UI_ACTION_RELEASE',
					'type': 'text',
					'title': '',
					'value': cuia_param,
					'div_class': div_class2x,
					'advanced': True
				}
				cuia_name, cuia_param = self.get_cuia(base_name + '__UI_LONG')
				config[base_name + '__UI_LONG__CUIA_NAME'] = {
					'enabling_options': 'UI_ACTION_RELEASE',
					'type': 'select',
					'title': 'Long-push',
					'value': cuia_name,
					'options': cuia_list,
					'div_class': div_class2,
					'advanced': True
				}
				config[base_name + '__UI_LONG__CUIA_PARAM'] = {
					'enabling_options': 'UI_ACTION_RELEASE',
					'type': 'text',
					'title': '',
					'value': cuia_param,
					'div_class': div_class2x,
					'advanced': True
				}

				config[base_name + '__MIDI_CHAN'] = {
					'enabling_options': 'MIDI_CC MIDI_CC_SWITCH MIDI_NOTE MIDI_PROG_CHANGE CVGATE_IN CVGATE_OUT GATE_OUT',
					'type': 'select',
					'title': 'MIDI Channel',
					'value': os.environ.get(base_name + '__MIDI_CHAN'),
					'options': ["Active"] + [str(j) for j in range(1,17)],
					'div_class': div_class1,
					'advanced': True
				}
				config[base_name + '__MIDI_NUM'] = {
					'enabling_options': 'MIDI_CC MIDI_CC_SWITCH MIDI_NOTE MIDI_PROG_CHANGE GATE_OUT',
					'type': 'select',
					'title': 'MIDI Number/Note',
					'value': os.environ.get(base_name + '__MIDI_NUM'),
					'options': [str(j) for j in range(0,128)],
					'div_class': div_class1,
					'advanced': True
				}
				config[base_name + '__MIDI_VAL'] = {
					'enabling_options': 'MIDI_CC MIDI_NOTE CVGATE_IN',
					'type': 'select',
					'title': 'MIDI Value/Velocity',
					'value': os.environ.get(base_name + '__MIDI_VAL', 127),
					'options': [str(j) for j in range(0,128)],
					'div_class': div_class1,
					'advanced': True
				}
				config[base_name + '__CV_CHAN'] = {
					'enabling_options': 'CVGATE_IN CVGATE_OUT',
					'type': 'select',
					'title': 'CV Channel',
					'value': str(cvchan),
					'options': ['0', '1', '2', '3'],
					'option_labels': {
						'0': '1',
						'1': '2',
						'2': '3',
						'3': '4'
					},
					'refresh_on_change': True,
					'div_class': div_class1,
					'advanced': True
				}
				# Add Separator
				config['_SEP_SW_{}_'.format(i)] = {
					'type': 'html',
					'content': "<hr>",
					'advanced': True
				}

		# Zynaptik ADC input
		if "4xAD" in zynaptik_config:
			config['_SECTION_ZYNAPTIK_AD_'] = {
				'type': 'html',
				'content': "<h3>Zynaptik Analog Input</h3>",
				'advanced': True
			}
			for i in range(0, 4):
				base_name = 'ZYNTHIAN_WIRING_ZYNAPTIK_AD{:02d}'.format(i+1)
				if i in cvgate_in:
					config['_ZYNAPTIK_AD{:02d}_'.format(i+1)] = {
						'type': 'html',
						'content': "<label>AD-{} Action</label>: Reserved for CV/Gate<br>".format(i+1),
						'advanced': True
					}
					config[base_name] = {
						'type': 'hidden',
						'value': "CVGATE_IN",
						'advanced': True
					}
				else:
					config[base_name] = {
						'type': 'select',
						'title': 'AD-{} Action'.format(i+1),
						'value': os.environ.get(base_name),
						'options': ZynSensorActionType,
						'div_class': div_class,
						'advanced': True
					}
					config[base_name + '__MIDI_CHAN'] = {
						'enabling_options': 'MIDI_CC MIDI_PITCH_BEND MIDI_CHAN_PRESS',
						'type': 'select',
						'title': 'Channel',
						'value': os.environ.get(base_name + '__MIDI_CHAN'),
						'options': ["Active"] + [str(j) for j in range(1,17)],
						'div_class': div_class1,
						'advanced': True
					}
					config[base_name + '__MIDI_NUM'] = {
						'enabling_options': 'MIDI_CC',
						'type': 'select',
						'title': 'Number',
						'value': os.environ.get(base_name + '__MIDI_NUM'),
						'options': [str(j) for j in range(0,128)],
						'div_class': div_class1,
						'advanced': True
					}
				# Add Separator
				config['_SEP_AD_{}_'.format(i)] = {
					'type': 'html',
					'content': "<hr>",
					'advanced': True
				}

		# Zynaptik DAC output
		if "4xDA" in zynaptik_config:
			config['_SECTION_ZYNAPTIK_DA_'] = {
				'type': 'html',
				'content': "<h3>Zynaptik Analog Output</h3>",
				'advanced': True
			}
			for i in range(0, 4):
				base_name = 'ZYNTHIAN_WIRING_ZYNAPTIK_DA{:02d}'.format(i+1)
				if i in cvgate_out:
					config['_ZYNAPTIK_DA{:02d}_'.format(i+1)] = {
						'type': 'html',
						'content': "<label>DA-{} Action</label>: Reserved for CV/Gate<br>".format(i+1),
						'advanced': True
					}
					config[base_name] = {
						'type': 'hidden',
						'value': "CVGATE_OUT",
						'advanced': True
					}
				else:
					config[base_name] = {
						'type': 'select',
						'title': 'DA-{} Action'.format(i+1),
						'value': os.environ.get(base_name),
						'options': ZynSensorActionType,
						'div_class': div_class,
						'advanced': True
					}
					config[base_name + '__MIDI_CHAN'] = {
						'enabling_options': 'MIDI_CC MIDI_PITCH_BEND MIDI_CHAN_PRESS',
						'type': 'select',
						'title': 'Channel',
						'value': os.environ.get(base_name + '__MIDI_CHAN'),
						'options': ["Active"] + [str(j) for j in range(1,17)],
						'div_class': div_class1,
						'advanced': True
					}
					config[base_name + '__MIDI_NUM'] = {
						'enabling_options': 'MIDI_CC',
						'type': 'select',
						'title': 'Number',
						'value': os.environ.get(base_name + '__MIDI_NUM'),
						'options': [str(j) for j in range(0,128)],
						'div_class': div_class1,
						'advanced': True
					}
				# Add Separator
				config['_SEP_DA_{}_'.format(i)] = {
					'type': 'html',
					'content': "<hr>",
					'advanced': True
				}

		# Zyntof input (Distance Sensor)
		if zyntof_config:
			n_zyntofs = int(zyntof_config)
			config['_SECTION_ZYNTOF_'] = {
				'type': 'html',
				'content': "<h3>Distance Sensors</h3>",
				'advanced': True
			}
			for i in range(0, n_zyntofs):
				base_name = 'ZYNTHIAN_WIRING_ZYNTOF{:02d}'.format(i+1)
				config[base_name] = {
					'type': 'select',
					'title': 'TOF-{} Action'.format(i+1),
					'value': os.environ.get(base_name),
					'options': ZynSensorActionType,
					'div_class': div_class,
					'advanced': True
				}
				config[base_name + '__MIDI_CHAN'] = {
					'enabling_options': 'MIDI_CC MIDI_PITCH_BEND MIDI_CHAN_PRESS',
					'type': 'select',
					'title': 'Channel',
					'value': os.environ.get(base_name + '__MIDI_CHAN'),
					'options': ["Active"] + [str(j) for j in range(1,17)],
					'div_class': div_class1,
					'advanced': True
				}
				config[base_name + '__MIDI_NUM'] = {
					'enabling_options': 'MIDI_CC',
					'type': 'select',
					'title': 'Number',
					'value': os.environ.get(base_name + '__MIDI_NUM'),
					'options': [str(j) for j in range(0,128)],
					'div_class': div_class1,
					'advanced': True
				}
				# Add Separator
				config['_SEP_ZT_{}_'.format(i)] = {
					'type': 'html',
					'content': "<hr>",
					'advanced': True
				}

		# Add Spacer
		config['_SPACER_'] = {
			'type': 'html',
			'content': "<br>"
		}

		super().get("Wiring", config, errors)


	@tornado.web.authenticated
	def post(self):
		command = self.get_argument('_command', '')
		logging.info("COMMAND = {}".format(command))
		self.request_data = self.get_request_data()
		if command == 'REFRESH':
			errors = None
			self.current_custom_profile = self.get_argument('ZYNTHIAN_WIRING_LAYOUT_CUSTOM_PROFILE', '')
			logging.debug("CURRENT CUSTOM PROFILE => {}".format(self.current_custom_profile))
			self.config_env(self.request_data)
			changed = self.get_argument('_changed', '')
			#logging.debug("CHANGED '{}'".format(changed))
			# If changed "wiring layout" => force loading custom profile from preset
			if changed == "ZYNTHIAN_WIRING_LAYOUT":
				try:
					for k, v in self.custom_profiles[self.current_custom_profile].items():
						os.environ[k] = v
				except:
					pass
		elif command == "SAVEAS":
			fname = self.get_argument('zynthian_wiring_layout_saveas_fname', '')
			errors = self.save_custom_profile(fname, self.request_data)
			self.current_custom_profile = fname
			self.load_custom_profiles()
			self.config_env(self.request_data)
		elif command == "DELETE":
			fname = self.get_argument('ZYNTHIAN_WIRING_LAYOUT_CUSTOM_PROFILE', '')
			errors = self.delete_custom_profile(fname)
			del(self.custom_profiles[fname])
			self.current_custom_profile = next(iter(self.custom_profiles.items()))[0]
			self.config_env(self.request_data)
		else:
			errors = self.update_config(self.request_data)

		self.get(errors)


	def get_request_data(self):
		data = tornado.escape.recursive_unicode(self.request.arguments)
		for i in range(64):
			base_name = 'ZYNTHIAN_WIRING_CUSTOM_SWITCH_{:02d}'.format(i + 1)
			for k in ("PUSH", "SHORT", "BOLD", "LONG"):
				base_subname = base_name + '__UI_' + k
				try:
					data[base_subname] = [data[base_subname + '__CUIA_NAME'][0] + " " + data[base_subname + '__CUIA_PARAM'][0]]
					del data[base_subname + '__CUIA_NAME']
					del data[base_subname + '__CUIA_PARAM']
				except:
					pass
		return data


	def update_config(self, data):
		# Check if restarting UI is needed
		ignore_varnames= [
			"LAYOUT_CUSTOM_PROFILE",
			"CUSTOM_SWITCH",
			"ZYNAPTIK_AD",
			"ZYNAPTIK_DA",
			"ZYNTOF",
		]
		for k in data:
			ignore = True
			if k.startswith("ZYNTHIAN_WIRING_"):
				ignore = False
				kk = k[16:]
			for ivn in ignore_varnames:
				if kk.startswith(ivn):
					ignore = True
					break
			if not ignore and data[k][0] != os.environ.get(k):
				logging.debug("Detected change in {} that needs restarting the UI: {} <> {}".format(k, data[k][0], os.environ.get(k)))
				self.restart_ui_flag = True
				break

		errors = super().update_config(data)

		if self.restart_ui_flag:
			self.rebuild_zyncoder()
		else:
			self.reload_wiring_layout_flag = True

		if self.reboot_flag:
			self.restart_ui_flag = False

		return errors


	@classmethod
	def complete_custom_profile(cls, data):
		res = OrderedDict()
		for i in range(36):
			base_name = "ZYNTHIAN_WIRING_CUSTOM_SWITCH_{:02d}".format(i+1)
			subvars = {
				"": "NONE",
				"__UI_PUSH": "NONE",
				"__UI_SHORT": "NONE",
				"__UI_BOLD": "NONE",
				"__UI_LONG": "NONE",
				"__MIDI_CHAN": "0",
				"__MIDI_NUM": "0",
				"__MIDI_VAL": "0",
				"__CV_CHAN": "0"
			}
			for sn,sv  in subvars.items():
				try:
					vname = base_name + sn
					if vname in data:
						res[vname] = data[vname]
					else:
						res[vname] = sv
				except Exception as e:
					logging.warning("Can't complete custom profile entry '{}' => {}".format(vname, e))

		for i in range(4):
			base_name = "ZYNTHIAN_WIRING_ZYNAPTIK_AD{:02d}".format(i+1)
			subvars = {
				"": "NONE",
				"__MIDI_CHAN": "0",
				"__MIDI_NUM": "0"
			}
			for sn,sv  in subvars.items():
				try:
					vname = base_name + sn
					if vname in data:
						res[vname] = data[vname]
					else:
						res[vname] = sv
				except Exception as e:
					logging.warning("Can't complete custom profile entry '{}' => {}".format(vname, e))

		for i in range(4):
			base_name = "ZYNTHIAN_WIRING_ZYNAPTIK_DA{:02d}".format(i+1)
			subvars = {
				"": "NONE",
				"__MIDI_CHAN": "0",
				"__MIDI_NUM": "0"
			}
			for sn,sv  in subvars.items():
				try:
					vname = base_name + sn
					if vname in data:
						res[vname] = data[vname]
					else:
						res[vname] = sv
				except Exception as e:
					logging.warning("Can't complete custom profile entry '{}' => {}".format(vname, e))

		for i in range(4):
			base_name = 'ZYNTHIAN_WIRING_ZYNTOF{:02d}'.format(i+1)
			subvars = {
				"": "NONE",
				"__MIDI_CHAN": "0",
				"__MIDI_NUM": "0"
			}
			for sn,sv  in subvars.items():
				try:
					vname = base_name + sn
					if vname in data:
						res[vname] = data[vname]
					else:
						res[vname] = sv
				except Exception as e:
					logging.warning("Can't complete custom profile entry '{}' => {}".format(vname, e))

		return res


	@classmethod
	def tweak_custom_profile(cls, data):
		for i in range(64):
			base_name = 'ZYNTHIAN_WIRING_CUSTOM_SWITCH_{:02d}'.format(i + 1)
			for k in ("PUSH", "SHORT", "BOLD", "LONG"):
				base_subname = base_name + '__UI_' + k
				try:
					parts = data[base_subname].split(" ", 2)
					data[base_subname + '__CUIA_NAME'] = parts[0]
					try:
						data[base_subname + '__CUIA_PARAM'] = parts[1]
					except:
						data[base_subname + '__CUIA_PARAM'] = ""
				except:
					pass
		return data


	# Load custom profiles
	def load_custom_profiles(self):
		self.custom_profiles = OrderedDict()
		p = re.compile("(\w*)=\"(.*)\"")

		self.custom_profiles[""] = OrderedDict()
		for fname in sorted(os.listdir(self.PROFILES_DIRECTORY)):
			profile_values = OrderedDict()
			fpath = "{}/{}".format(self.PROFILES_DIRECTORY,fname)
			try:
				with open(fpath) as f:
					for line in f:
						try:
							if line[0] == '#':
								continue
							m = p.match(line)
							if m:
								profile_values[m.group(1)] = m.group(2)
						except Exception as e:
							logging.warning("Invalid line in wiring custom profile '{}' will be ignored: {}\n{}".format(fpath, e, line))
				try:
					profile_values = WiringConfigHandler.complete_custom_profile(profile_values)
					self.custom_profiles[fname] = WiringConfigHandler.tweak_custom_profile(profile_values)
					logging.debug("LOADED WIRING CUSTOM PROFILE '{}'".format(fpath))
				except Exception as e:
					logging.warning("Can't complete wiring custom profile '{}': {}".format(fpath, e))
			except Exception as e:
				logging.warning("Invalid wiring custom profile '{}' will be ignored: {}".format(fpath, e))


	def save_custom_profile(self, fname, data):
		try:
			fpath = "{}/{}".format(self.PROFILES_DIRECTORY,fname)
			with open(fpath, "w") as f:
				for k,v in data.items():
					if k.startswith("ZYNTHIAN_WIRING_CUSTOM_SWITCH_") or k.startswith("ZYNTHIAN_WIRING_ZYNAPTIK") or k.startswith("ZYNTHIAN_WIRING_ZYNTOF"):
						f.write("{}=\"{}\"\n".format(k,v[0]))
			logging.debug("SAVED WIRING CUSTOM PROFILE '{}'".format(fpath))
		except Exception as e:
			logging.warning("Can't save wiring custom profile '{}': {}".format(fpath, e))


	def delete_custom_profile(self, fname):
		try:
			fpath = "{}/{}".format(self.PROFILES_DIRECTORY,fname)
			os.remove(fpath)
			logging.debug("DELETED WIRING CUSTOM PROFILE '{}'".format(fpath))
		except Exception as e:
			logging.warning("Can't delete wiring custom profile '{}': {}".format(fpath, e))


	@classmethod
	def rebuild_zyncoder(cls):
		try:
			cmd="cd %s/zyncoder/build;cmake ..;make" % os.environ.get('ZYNTHIAN_DIR')
			check_output(cmd, shell=True)
		except Exception as e:
			logging.error("Rebuilding Zyncoder Library: %s" % e)

	
	# Load and return a custom profile
	@classmethod
	def get_custom_profile(cls, fname):
		p = re.compile("(\w*)=\"(.*)\"")

		profile_values = OrderedDict()
		fpath = "{}/{}".format(cls.PROFILES_DIRECTORY,fname)
		try:
			with open(fpath) as f:
				for line in f:
					try:
						if line[0]=='#':
							continue
						m = p.match(line)
						if m:
							profile_values[m.group(1)] = m.group(2)
					except Exception as e:
						logging.warning("Invalid line in wiring custom profile '{}' will be ignored: {}\n{}".format(fpath, e, line))
			try:
				profile_values = cls.complete_custom_profile(profile_values)
				logging.debug("LOADED WIRING CUSTOM PROFILE '{}'".format(fpath))
			except Exception as e:
				logging.warning("Can't complete wiring custom profile '{}': {}".format(fpath, e))
		except Exception as e:
			logging.warning("Invalid wiring custom profile '{}' will be ignored: {}".format(fpath, e))

		return profile_values

