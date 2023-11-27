# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# MIDI Configuration Handler
#
# Copyright (C) 2017 Markus Heidt <markus@heidt-tech.com>
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
import jack
import logging
import tornado.web
from shutil import copyfile

from lib.zynthian_config_handler import ZynthianConfigHandler

import zynconf
from zyngine.zynthian_midi_filter import MidiFilterScript
from zyngui.zynthian_gui import zynthian_gui

# ------------------------------------------------------------------------------
# Module Methods
# ------------------------------------------------------------------------------


def get_ports_config(current_midi_ports=""):
	midi_ports = {'IN': [], 'OUT': [], 'FB': []}
	try:
		# Get MIDI ports list from jack
		client = jack.Client("ZynthianWebConf")
		#F or jack, output/input convention are reversed => output=readable, input=writable
		midi_in_ports = client.get_ports(is_midi=True, is_physical=True, is_output=True)
		midi_out_ports = client.get_ports(is_midi=True, is_physical=True, is_input=True)
		# Add QMidiNet ports
		qmidinet_in_ports = client.get_ports("QmidiNet", is_midi=True, is_physical=False, is_output=True)
		qmidinet_out_ports = client.get_ports("QmidiNet", is_midi=True, is_physical=False, is_input=True)
		try:
			midi_in_ports.append(qmidinet_in_ports[0])
			midi_out_ports.append(qmidinet_out_ports[0])
		except:
			pass

		# Add RTP-Midi ports
		rtpmidi_in_ports = client.get_ports("jackrtpmidid", is_midi=True, is_physical=False, is_output=True)
		rtpmidi_out_ports = client.get_ports("jackrtpmidid", is_midi=True, is_physical=False, is_input=True)
		try:
			midi_in_ports.append(rtpmidi_in_ports[0])
			midi_out_ports.append(rtpmidi_out_ports[0])
		except:
			pass

		# Add TouchOSC-Midi ports
		touchosc_in_ports = client.get_ports("TouchOSC Bridge", is_midi=True, is_physical=False, is_output=True)
		touchosc_out_ports = client.get_ports("TouchOSC Bridge", is_midi=True, is_physical=False, is_input=True)
		try:
			midi_in_ports.append(touchosc_in_ports[0])
			midi_out_ports.append(touchosc_out_ports[0])
		except:
			pass

		disabled_midi_in_ports = zynconf.get_disabled_midi_in_ports(current_midi_ports)
		enabled_midi_out_ports = zynconf.get_enabled_midi_out_ports(current_midi_ports)
		enabled_midi_fb_ports = zynconf.get_enabled_midi_fb_ports(current_midi_ports)

		# Generate MIDI_PORTS{IN,OUT,FB} configuration array
		for idx, midi_port in enumerate(midi_in_ports):
			alias = get_port_alias(midi_port)
			port_id = alias.replace(' ', '_')
			midi_ports['IN'].append({
				'name': midi_port.name,
				'shortname': midi_port.shortname,
				'alias': alias,
				'id': port_id,
				'checked': 'checked="checked"' if port_id not in disabled_midi_in_ports else ''
			})
		for idx, midi_port in enumerate(midi_out_ports):
			alias = get_port_alias(midi_port)
			port_id = alias.replace(' ', '_')
			midi_ports['OUT'].append({
				'name': midi_port.name,
				'shortname': midi_port.shortname,
				'alias': alias,
				'id': port_id,
				'checked': 'checked="checked"' if port_id in enabled_midi_out_ports else ''
			})
		for idx, midi_port in enumerate(midi_out_ports):
			alias = get_port_alias(midi_port)
			port_id = alias.replace(' ', '_')
			midi_ports['FB'].append({
				'name': midi_port.name,
				'shortname': midi_port.shortname,
				'alias': alias,
				'id': port_id,
				'checked': 'checked="checked"' if port_id in enabled_midi_fb_ports else ''
			})

	except Exception as e:
		logging.error("%s" % e)

	logging.debug("MIDI_PORTS => %s" % midi_ports)
	return midi_ports


def get_port_alias(midi_port):
	try:
		alias_id = '_'.join(midi_port.aliases[0].split('-')[5:])
	except:
		alias_id = midi_port.name

	if midi_port.is_input:
		postfix = "OUT"
	else:
		postfix = "IN"

	if alias_id.startswith("ttymidi:"):
		alias_id = f"DIN-5 MIDI-{postfix}"
	elif alias_id.startswith("a2j:"):
		alias_id = f"ALSA MIDI-{postfix}"
	elif alias_id == "f_midi":
		alias_id = f"USB MIDI-{postfix}"

	return alias_id


#------------------------------------------------------------------------------
# Midi Config Handler
#------------------------------------------------------------------------------

class MidiConfigHandler(ZynthianConfigHandler):
	PROFILES_DIRECTORY = "%s/midi-profiles" % os.environ.get("ZYNTHIAN_CONFIG_DIR")
	DEFAULT_MIDI_PORTS = "DISABLED_IN=\nENABLED_OUT=ttymidi:MIDI_out\nENABLED_FB="

	midi_channels = {
		"00": "None",
		"01": "01",
		"02": "02",
		"03": "03",
		"04": "04",
		"05": "05",
		"06": "06",
		"07": "07",
		"08": "09",
		"10": "10",
		"11": "11",
		"12": "12",
		"13": "13",
		"14": "14",
		"15": "15",
		"16": "16"
	}

	midi_program_change_presets = {
		'Custom': {
			'ZYNTHIAN_MIDI_MASTER_PROGRAM_CHANGE_UP': '',
			'ZYNTHIAN_MIDI_MASTER_PROGRAM_CHANGE_DOWN': '',
			'ZYNTHIAN_MIDI_MASTER_BANK_CHANGE_UP': '',
			'ZYNTHIAN_MIDI_MASTER_BANK_CHANGE_DOWN': ''
		},
		'Roland MSB': {
			'ZYNTHIAN_MIDI_MASTER_PROGRAM_CHANGE_UP': 'C#7F',
			'ZYNTHIAN_MIDI_MASTER_PROGRAM_CHANGE_DOWN': 'C#00',
			'ZYNTHIAN_MIDI_MASTER_BANK_CHANGE_UP': 'B#007F',
			'ZYNTHIAN_MIDI_MASTER_BANK_CHANGE_DOWN': 'B#0000',
			'ZYNTHIAN_MIDI_MASTER_BANK_CHANGE_CCNUM': '0'
		},
		'Roland LSB': {
			'ZYNTHIAN_MIDI_MASTER_PROGRAM_CHANGE_UP': 'C#7F',
			'ZYNTHIAN_MIDI_MASTER_PROGRAM_CHANGE_DOWN': 'C#00',
			'ZYNTHIAN_MIDI_MASTER_BANK_CHANGE_UP': 'B#207F',
			'ZYNTHIAN_MIDI_MASTER_BANK_CHANGE_DOWN': 'B#2000',
			'ZYNTHIAN_MIDI_MASTER_BANK_CHANGE_CCNUM': '32'
		}
	}

	program_change_mode_labels = {
		'0': 'MSB',
		'32': 'LSB'
	}

	midi_cc_labels = {
		'0': '00 - Bank Select (MSB)',
		'1': '01 - Modulation Wheel (MSB)',
		'2': '02 - Breath controller (MSB)',
		'3': '03 - Undefined',
		'4': '04 - Foot Pedal (MSB)',
		'5': '05 - Portamento Time (MSB)',
		'6': '06 - Data Entry (MSB)',
		'7': '07 - Volume (MSB)',
		'8': '08 - Balance (MSB)',
		'9': '09 - Undefined',
		'10': '10 - Pan Position (MSB)',
		'11': '11 - Expression (MSB)',
		'12': '12 - Effect Controller 1 (MSB)',
		'13': '13 - Effect Controller 2 (MSB)',
		'14': '14 - Undefined',
		'15': '15 - Undefined',
		'16': '16 - General Purpose Controller 1',
		'17': '17 - General Purpose Controller 2',
		'18': '18 - General Purpose Controller 3',
		'19': '19 - General Purpose Controller 4',
		'20': '20 - Undefined',
		'21': '21 - Undefined',
		'22': '22 - Undefined',
		'23': '23 - Undefined',
		'24': '24 - Undefined',
		'25': '25 - Undefined',
		'26': '26 - Undefined',
		'27': '27 - Undefined',
		'28': '28 - Undefined',
		'29': '29 - Undefined',
		'30': '30 - Undefined',
		'31': '31 - Undefined',
		'32': '32 - Bank Select (LSB)',
		'33': '33 - Modulation Wheel (LSB)',
		'34': '34 - Breath controller (LSB)',
		'35': '35 - LSB CC#03 (Undefined)',
		'36': '36 - Foot Pedal (LSB)',
		'37': '37 - Portamento Time (LSB)',
		'38': '38 - Data Entry (LSB)',
		'39': '39 - Volume (LSB)',
		'40': '40 - Balance (LSB)',
		'41': '41 - LSB CC#09 (Undefined)',
		'42': '42 - Pan Position (LSB)',
		'43': '43 - Expression (LSB)',
		'44': '44 - Effect Controller 1 (LSB)',
		'45': '45 - Effect Controller 2 (LSB)',
		'46': '46 - LSB CC#14 (Undefined)',
		'47': '47 - LSB CC#15 (Undefined)',
		'48': '48 - LSB CC#16 (GP Controller 1)',
		'49': '49 - LSB CC#17 (GP Controller 2)',
		'50': '50 - LSB CC#18 (GP Controller 3)',
		'51': '51 - LSB CC#19 (GP Controller 4)',
		'52': '52 - LSB CC#20 (Undefined)',
		'53': '53 - LSB CC#21 (Undefined)',
		'54': '54 - LSB CC#22 (Undefined)',
		'55': '55 - LSB CC#23 (Undefined)',
		'56': '56 - LSB CC#24 (Undefined)',
		'57': '57 - LSB CC#25 (Undefined)',
		'58': '58 - LSB CC#26 (Undefined)',
		'59': '59 - LSB CC#27 (Undefined)',
		'60': '60 - LSB CC#28 (Undefined)',
		'61': '61 - LSB CC#29 (Undefined)',
		'62': '62 - LSB CC#30 (Undefined)',
		'63': '63 - LSB CC#31 (Undefined)',
		'64': '64 - Sustain Pedal On/Off',
		'65': '65 - Portamento On/Off',
		'66': '66 - Sostenuto On/Off',
		'67': '67 - Soft Pedal On/Off',
		'68': '68 - Legato On/Off',
		'69': '69 - Hold 2',
		'70': '70 - SC-1: Sound Variation',
		'71': '71 - SC-2: Timbre/Harmonic Intens./VCF Resonance',
		'72': '72 - SC-3: Release Time/VCA Release',
		'73': '73 - SC-4: Attack Time',
		'74': '74 - SC-5: Brightness/VCF Cutoff Freq.',
		'75': '75 - SC-6: Decay Time',
		'76': '76 - SC-7: Vibrato Rate',
		'77': '77 - SC-8: Vibrato Depth',
		'78': '78 - SC-9: Vibrato Delay',
		'79': '79 - SC-10: Undefined',
		'80': '80 - General Purpose Controller 5',
		'81': '81 - General Purpose Controller 6',
		'82': '82 - General Purpose Controller 7',
		'83': '83 - General Purpose Controller 8',
		'84': '84 - Portamento Control',
		'85': '85 - Undefined',
		'86': '86 - Undefined',
		'87': '87 - Undefined',
		'88': '88 - High Resolution Velocity Prefix',
		'89': '89 - Undefined',
		'90': '90 - Undefined',
		'91': '91 - Effects 1 Depth (Ext. Effect Depth)',
		'92': '92 - Effects 2 Depth (Tremelo Depth)',
		'93': '93 - Effects 3 Depth (Chorus Depth)',
		'94': '94 - Effects 4 Depth (Detune Depth)',
		'95': '95 - Effects 5 Depth (Phaser Depth)',
		'96': '96 - Data Increment',
		'97': '97 - Data Decrement',
		'98': '98 - NRPN number (LSB)',
		'99': '99 - NRPN number (MSB)',
		'100': '100 - RPN number (LSB)',
		'101': '101 - RPN number (MSB)',
		'102': '102 - Undefined',
		'103': '103 - Undefined',
		'104': '104 - Undefined',
		'105': '105 - Undefined',
		'106': '106 - Undefined',
		'107': '107 - Undefined',
		'108': '108 - Undefined',
		'109': '109 - Undefined',
		'110': '110 - Undefined',
		'111': '111 - Undefined',
		'112': '112 - Undefined',
		'113': '113 - Undefined',
		'114': '114 - Undefined',
		'115': '115 - Undefined',
		'116': '116 - Undefined',
		'117': '117 - Undefined',
		'118': '118 - Undefined',
		'119': '119 - Undefined',
		'120': '120 - All Sound Off',
		'121': '121 - Reset All Controllers',
		'122': '122 - Local On/Off Switch',
		'123': '123 - All Notes Off',
		'124': '124 - Omni Mode Off',
		'125': '125 - Omni Mode On',
		'126': '126 - Mono Mode',
		'127': '127 - Poly Mode'
	}

	midi_event_types = {
		'NON': 'Note-On',
		'NOFF': 'Note-Off',
		'PC': 'Program Change',
		'CC': 'Continuous Controller Change (CC)',
		'KP': 'Polyphonic Key Pressure (Aftertouch)',
		'CP': 'Channel Pressure (Aftertouch)',
		'PB': 'Pitch Bending'
	}

	def prepare(self):
		super().prepare()
		self.current_midi_profile_script = None
		self.load_midi_profile_directories()

	@tornado.web.authenticated
	def get(self, errors=None):
		self.load_midi_profiles()

		#Get current MIDI ports configuration
		current_midi_ports = self.get_midi_env('ZYNTHIAN_MIDI_PORTS', self.DEFAULT_MIDI_PORTS)
		current_midi_ports = current_midi_ports.replace("\\n", "\n")
		#logging.debug("MIDI_PORTS = %s" % current_midi_ports)
		ports_config = {'MIDI_PORTS': get_ports_config(current_midi_ports)}

		mfr_config = {
			'RULE_EVENT_TYPES': {
				'options': list(self.midi_event_types.keys()),
				'option_labels': self.midi_event_types
			},
			'RULE_CC_NUMS': {
				'option_labels': self.midi_cc_labels
			}
		}

		cuia_list = [""] + zynthian_gui.get_cuia_list()
		current_note_cuia_text = self.get_midi_env('ZYNTHIAN_MIDI_MASTER_NOTE_CUIA', '')
		if current_note_cuia_text:
			current_note_cuia = {}
			for row in current_note_cuia_text.split("\\n"):
				parts = row.strip().split(':')
				if len(parts) > 1:
					current_note_cuia[parts[0].strip()] = parts[1].strip()
		else:
			current_note_cuia_text = ""
			current_note_cuia = zynconf.NoteCuiaDefault
			for note, cuia in current_note_cuia.items():
				current_note_cuia_text += "{}: {}\n".format(note, cuia)
		mmncuia_config = {'CUIA_LIST': cuia_list, 'CURRENT_NOTE_CUIA': current_note_cuia}

		# upper case ZYNTHIAN_MIDI will be stored in profile file
		# other upper case in zynthian_envar
		config = {
			'ZYNTHIAN_SCRIPT_MIDI_PROFILE': {
				'type': 'select',
				'title': 'MIDI profile',
				'value': self.current_midi_profile_script,
				'options': self.midi_profile_scripts,
				'option_labels': {script_name: os.path.basename(script_name).split('.')[0] for script_name in self.midi_profile_scripts},
				'presets': self.midi_profile_presets,
				'div_class': "col-xs-8"
			},
			'zynthian_midi_profile_saveas_script': {
				'type': 'button',
				'title': 'Save as ...',
				'button_type': 'button',
				'class': 'btn-theme btn-block',
				'icon': 'fa fa-plus',
				'script_file': 'midi_profile_saveas.js',
				'div_class': "col-xs-2",
				'inline': 1
			},
			'zynthian_midi_profile_delete_script': {
				'type': 'button',
				'title': 'Delete',
				'button_type': 'submit',
				'class': 'btn-danger btn-block',
				'icon': 'fa fa-trash-o',
				'script_file': 'midi_profile_delete.js',
				'div_class': "col-xs-2",
				'inline': 1
			},
			'zynthian_midi_profile_saveas_fname': {
				'type': 'hidden',
				'value': ''
			},
			'ZYNTHIAN_MIDI_PROG_CHANGE_ZS3': {
				'type': 'boolean',
				'title': 'Program Change ZS3 (Program Change for SubSnapShots)',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_PROG_CHANGE_ZS3', '1'),
				'advanced': False
			},
			'ZYNTHIAN_MIDI_BANK_CHANGE': {
				'type': 'boolean',
				'title': 'Bank Change with CC#0(MSB) & CC#32(LSB)',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_BANK_CHANGE', '0'),
				'advanced': False
			},
			'ZYNTHIAN_MIDI_PRESET_PRELOAD_NOTEON': {
				'type': 'boolean',
				'title': 'Preload Presets with Note-On events',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_PRESET_PRELOAD_NOTEON', '1'),
				'advanced': False
			},
			'ZYNTHIAN_MIDI_FILTER_OUTPUT': {
				'type': 'boolean',
				'title': 'Route MIDI to Output Ports',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_FILTER_OUTPUT', '1'),
				'advanced': False
			},
			'ZYNTHIAN_MIDI_SYS_ENABLED': {
				'type': 'boolean',
				'title': 'Enable System Messages (Transport)',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_SYS_ENABLED', '1'),
				'advanced': False
			},
			'ZYNTHIAN_MIDI_CC_AUTOMODE': {
				'type': 'boolean',
				'title': 'Autodetect CC relative mode',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_CC_AUTOMODE', '1'),
				'advanced': True
			},
			'ZYNTHIAN_MIDI_RTPMIDI_ENABLED': {
				'type': 'boolean',
				'title': 'Enable RTP-MIDI (AppleMIDI network)',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_RTPMIDI_ENABLED', '0'),
				'advanced': False
			},
			'ZYNTHIAN_MIDI_NETWORK_ENABLED': {
				'type': 'boolean',
				'title': 'Enable QmidiNet (IP Multicast)',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_NETWORK_ENABLED', '0'),
				'advanced': False
			},
			'ZYNTHIAN_MIDI_TOUCHOSC_ENABLED': {
				'type': 'boolean',
				'title': 'Enable TouchOSC MIDI Bridge',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_TOUCHOSC_ENABLED', '0'),
				'advanced': False
			},
			'ZYNTHIAN_MIDI_AUBIONOTES_ENABLED': {
				'type': 'boolean',
				'title': 'Enable AubioNotes (Audio2MIDI)',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_AUBIONOTES_ENABLED', '0'),
				'advanced': True
			},
			'ZYNTHIAN_MIDI_FINE_TUNING': {
				'type': 'text',
				'title': 'MIDI fine tuning (Hz)',
				'value':  self.get_midi_env('ZYNTHIAN_MIDI_FINE_TUNING', '440.0'),
				#'options': map(lambda x: str(x).zfill(2), list(range(392, 493)))
				'advanced': False
			},
			'ZYNTHIAN_MIDI_PORTS': {
				'type': 'textarea',
				'title': 'MIDI Ports',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_PORTS'),
				'cols': 50,
				'rows': 2,
				'addButton': 'display_midi_ports_panel',
				'addPanel': 'midi_ports.html',
				'addPanelConfig': ports_config,
				'advanced': False
			},
			'ZYNTHIAN_MIDI_FILTER_RULES': {
				'type': 'textarea',
				'title': 'Midi filter rules',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_FILTER_RULES'),
				'cols': 50,
				'rows': 5,
				'addButton': 'display_midi_filter_rule_panel',
				'addPanel': 'midi_filter_rule.html',
				'addPanelConfig': mfr_config,
				'advanced': True
			},
			'_SECTION_MASTER_CHANNEL_': {
				'type': 'html',
				'content': "<h3>Master Channel</h3>",
				'advanced': True
			},
			'ZYNTHIAN_MIDI_MASTER_CHANNEL': {
				'type': 'select',
				'title': 'Master MIDI channel',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_MASTER_CHANNEL', '0'),
				'options': list(self.midi_channels.keys()),
				'option_labels': self.midi_channels,
				'advanced': True
			},
			'ZYNTHIAN_MIDI_MASTER_PROGRAM_CHANGE_TYPE': {
				'type': 'select',
				'title': 'Master change type',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_MASTER_PROGRAM_CHANGE_TYPE'),
				'options': list(self.midi_program_change_presets.keys()),
				'presets': self.midi_program_change_presets,
				'advanced': True
			},
			'ZYNTHIAN_MIDI_MASTER_BANK_CHANGE_CCNUM': {
				'type': 'select',
				'title': 'Master Bank change mode',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_MASTER_BANK_CHANGE_CCNUM'),
				'options': list(self.program_change_mode_labels.keys()),
				'option_labels': self.program_change_mode_labels,
				'advanced': True
			},
			'ZYNTHIAN_MIDI_MASTER_PROGRAM_CHANGE_UP': {
				'type': 'text',
				'title': 'Master Program change-up',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_MASTER_PROGRAM_CHANGE_UP'),
				'advanced': True
			},
			'ZYNTHIAN_MIDI_MASTER_PROGRAM_CHANGE_DOWN': {
				'type': 'text',
				'title': 'Master Program change-down',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_MASTER_PROGRAM_CHANGE_DOWN'),
				'advanced': True
			},
			'ZYNTHIAN_MIDI_MASTER_BANK_CHANGE_UP': {
				'type': 'text',
				'title': 'Master Bank change-up',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_MASTER_BANK_CHANGE_UP'),
				'advanced': True
			},
			'ZYNTHIAN_MIDI_MASTER_BANK_CHANGE_DOWN': {
				'type': 'text',
				'title': 'Master Bank change-down',
				'value': self.get_midi_env('ZYNTHIAN_MIDI_MASTER_BANK_CHANGE_DOWN'),
				'advanced': True
			},
			'ZYNTHIAN_MIDI_MASTER_NOTE_CUIA': {
				'type': 'textarea',
				'title': 'Master Key Actions',
				'value': current_note_cuia_text,
				'cols': 50,
				'rows': 4,
				'addButton': 'display_midi_master_note_cuia_panel',
				'addPanel': 'midi_master_note_cuia.html',
				'addPanelConfig': mmncuia_config,
				'advanced': True
			}
		}
		super().get("MIDI Options", config, errors)

	@tornado.web.authenticated
	def post(self):
		self.request.arguments['ZYNTHIAN_MIDI_FILTER_OUTPUT'] = self.request.arguments.get('ZYNTHIAN_MIDI_FILTER_OUTPUT', '0')
		self.request.arguments['ZYNTHIAN_MIDI_SYS_ENABLED'] = self.request.arguments.get('ZYNTHIAN_MIDI_SYS_ENABLED', '0')
		self.request.arguments['ZYNTHIAN_MIDI_CC_AUTOMODE'] = self.request.arguments.get('ZYNTHIAN_MIDI_CC_AUTOMODE', '0')
		self.request.arguments['ZYNTHIAN_MIDI_PRESET_PRELOAD_NOTEON'] = self.request.arguments.get('ZYNTHIAN_MIDI_PRESET_PRELOAD_NOTEON', '0')
		self.request.arguments['ZYNTHIAN_MIDI_PROG_CHANGE_ZS3'] = self.request.arguments.get('ZYNTHIAN_MIDI_PROG_CHANGE_ZS3', '0')
		self.request.arguments['ZYNTHIAN_MIDI_BANK_CHANGE'] = self.request.arguments.get('ZYNTHIAN_MIDI_BANK_CHANGE', '0')
		self.request.arguments['ZYNTHIAN_MIDI_RTPMIDI_ENABLED'] = self.request.arguments.get('ZYNTHIAN_MIDI_RTPMIDI_ENABLED', '0')
		self.request.arguments['ZYNTHIAN_MIDI_NETWORK_ENABLED'] = self.request.arguments.get('ZYNTHIAN_MIDI_NETWORK_ENABLED', '0')
		self.request.arguments['ZYNTHIAN_MIDI_TOUCHOSC_ENABLED'] = self.request.arguments.get('ZYNTHIAN_MIDI_TOUCHOSC_ENABLED', '0')
		self.request.arguments['ZYNTHIAN_MIDI_AUBIONOTES_ENABLED'] = self.request.arguments.get('ZYNTHIAN_MIDI_AUBIONOTES_ENABLED', '0')
		self.request.arguments['ZYNTHIAN_MIDI_MASTER_CHANNEL'] = self.request.arguments.get('ZYNTHIAN_MIDI_MASTER_CHANNEL', '0')
		self.request.arguments['ZYNTHIAN_MIDI_PORTS'] = self.request.arguments.get('ZYNTHIAN_MIDI_PORTS', '0')

		escaped_request_arguments = tornado.escape.recursive_unicode(self.request.arguments)

		errors = {}

		try:
			freq = float(self.request.arguments.get('ZYNTHIAN_MIDI_FINE_TUNING', '440.0')[0])
			if freq < 392.0 or freq > 493.88:
				errors['ZYNTHIAN_MIDI_FINE_TUNING'] = "Frequency must be in the range 392.00 - 493.88 Hz!"
		except:
			self.request.arguments['ZYNTHIAN_MIDI_FINE_TUNING'] = 440.0
			errors['ZYNTHIAN_MIDI_FINE_TUNING'] = "Frequency must be a number!"

		filter_error = self.validate_filter_rules(escaped_request_arguments)
		if filter_error:
			errors['ZYNTHIAN_MIDI_FILTER_RULES'] = filter_error

		if not errors:
			# remove fields that start with FILTER_ADD from request_args, so that they won't be passed to update_config
			for filter_add_argument in list(escaped_request_arguments.keys()):
				if filter_add_argument.startswith('FILTER_ADD'):
					del escaped_request_arguments[filter_add_argument]

			profile_saveas_fname = self.get_argument('zynthian_midi_profile_saveas_fname')

			if profile_saveas_fname:
				# New MIDI profile
				self.current_midi_profile_script = self.PROFILES_DIRECTORY + '/' + profile_saveas_fname + '.sh'
				try:
					# create file as copy of default:
					zynconf.get_midi_config_fpath(self.current_midi_profile_script)
					zynconf.update_midi_profile(escaped_request_arguments, self.current_midi_profile_script)
					mode = os.stat(self.current_midi_profile_script).st_mode
					mode |= (mode & 0o444) >> 2	 # copy R bits to X
					os.chmod(self.current_midi_profile_script, mode)
					errors = zynconf.save_config({'ZYNTHIAN_SCRIPT_MIDI_PROFILE': self.current_midi_profile_script})
					self.load_midi_profile_directories()
				except:
					errors['zynthian_midi_profile_saveas_script'] = "Can't create new profile!"

			elif 'zynthian_midi_profile_delete_script' in self.request.arguments and self.get_argument('zynthian_midi_profile_delete_script') == "1":
				# DELETE
				if self.current_midi_profile_script.startswith(self.PROFILES_DIRECTORY):
					os.remove(self.current_midi_profile_script)
					self.current_midi_profile_script = "{}/default.sh".format(self.PROFILES_DIRECTORY)
					errors = zynconf.save_config({'ZYNTHIAN_SCRIPT_MIDI_PROFILE': self.current_midi_profile_script})
					self.load_midi_profile_directories()
				else:
					errors['zynthian_midi_profile_delete_script'] = 'You are allowed to delete user profiles only!'

			else:
				# SAVE
				if self.current_midi_profile_script:
					update_parameters = []
					for parameter in escaped_request_arguments:
						if not parameter.startswith('ZYNTHIAN_'):
							update_parameters.append(parameter)

					for k in update_parameters:
						del escaped_request_arguments[k]

					zynconf.update_midi_profile(escaped_request_arguments, self.current_midi_profile_script)
					errors = self.update_config(escaped_request_arguments)
				else:
					errors['zynthian_midi_profile_new_script_name'] = 'No profile name!'

			self.reload_midi_config_flag = True

		self.get(errors)

	def load_midi_profile_directories(self):
		# Get profiles list
		self.midi_profile_scripts = ["%s/%s" % (self.PROFILES_DIRECTORY, x) for x in os.listdir(self.PROFILES_DIRECTORY)]
		# If list is empty ...
		if len(self.midi_profile_scripts) == 0:
			self.current_midi_profile_script = "%s/default.sh" % self.PROFILES_DIRECTORY
			self.midi_profile_scripts = [self.current_midi_profile_script]
			try:
				# Try to copy from default template
				default_src = "%s/config/default_midi_profile.sh" % os.getenv('ZYNTHIAN_SYS_DIR', "/zynthian/zynthian-sys")
				copyfile(default_src, self.current_midi_profile_script)
			except Exception as e:
				logging.error(e)
		# Else, get active profile
		else:
			if not self.current_midi_profile_script:
				if 'ZYNTHIAN_SCRIPT_MIDI_PROFILE' in self.request.arguments:
					self.current_midi_profile_script = self.get_argument('ZYNTHIAN_SCRIPT_MIDI_PROFILE')
				else:
					self.current_midi_profile_script = os.getenv('ZYNTHIAN_SCRIPT_MIDI_PROFILE', self.midi_profile_scripts[0])
			if self.current_midi_profile_script not in self.midi_profile_scripts:
				self.current_midi_profile_script = self.midi_profile_scripts[0]

	@staticmethod
	def validate_filter_rules(escaped_request_arguments):
		if escaped_request_arguments['ZYNTHIAN_MIDI_FILTER_RULES'][0]:
			new_line = escaped_request_arguments['ZYNTHIAN_MIDI_FILTER_RULES'][0]
			try:
				MidiFilterScript(new_line, False)
			except Exception as e:
				return "ERROR parsing MIDI filter rule: " + str(e)

	def load_midi_profiles(self):
		self.midi_profile_presets = {}
		p = re.compile("export (\w*)=\"(.*)\"")
		invalid_files = []
		for midi_profile_script in self.midi_profile_scripts:
			#logging.info(midi_profile_script)
			profile_values = {}
			try:
				with open(midi_profile_script) as f:
					for line in f:
						if line[0] == '#':
							continue
						m = p.match(line)
						if m:
							profile_values[m.group(1)] = m.group(2)
				self.midi_profile_presets[midi_profile_script] = profile_values
				logging.debug("LOADED MIDI PROFILE %s" % midi_profile_script)
			except:
				invalid_files.append(midi_profile_script)

		for midi_profile_script in invalid_files:
			logging.warning("Invalid MIDI profile will be ignored: " + midi_profile_script)
			self.midi_profile_scripts.remove(midi_profile_script)

		if self.current_midi_profile_script:
			self.midi_envs = self.midi_profile_presets[self.current_midi_profile_script]
		else:
			self.midi_envs = {}

	def get_midi_env(self, key, default=''):
		if key in self.midi_envs:
			return self.midi_envs[key]
		else:
			return default
