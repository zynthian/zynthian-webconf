import os
import tornado.web
import logging
from collections import OrderedDict
from subprocess import check_output
from lib.ZynthianConfigHandler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# System Menu
#------------------------------------------------------------------------------

class MidiConfigHandler(ZynthianConfigHandler):

	midi_program_change_presets=OrderedDict([
		['Custom', {
			'ZYNTHIAN_MASTER_MIDI_PROGRAM_CHANGE_UP': '',
			'ZYNTHIAN_MASTER_MIDI_PROGRAM_CHANGE_DOWN': '',
			'ZYNTHIAN_MASTER_MIDI_BANK_CHANGE_UP': '',
			'ZYNTHIAN_MASTER_MIDI_BANK_CHANGE_DOWN': ''
		}],
		['Roland', {
			'ZYNTHIAN_MASTER_MIDI_PROGRAM_CHANGE_UP': 'C#7F',
			'ZYNTHIAN_MASTER_MIDI_PROGRAM_CHANGE_DOWN': 'C#00',
			'ZYNTHIAN_MASTER_MIDI_BANK_CHANGE_UP': 'B#007F',
			'ZYNTHIAN_MASTER_MIDI_BANK_CHANGE_DOWN': 'B#0000'
		}]
	])

	program_change_mode_labels=OrderedDict([
		['2', 'LSB'],
		['0', 'MSB']
	])

	midi_cc_labels=OrderedDict([
		['1', '1 - Modulation Wheel'],
		['2', '2 - Breath controller'],
		['4', '4 - Foot Pedal'],
		['5', '5 - Portamento Time'],
		['6', '6 - Data Entry'],
		['7', '7 - Volume'],
		['10', '10 - Pan Position']
	])

	midi_event_options=OrderedDict([
		['PG', 'Program change'],
		['KP', 'Polyphonic Key Pressure (Aftertouch)'],
		['CP', 'Channel Pressure (Aftertouch)'],
		['PB', 'Pitch Bending'],
		['CC', 'Continuous Controller Change']
	])

	@tornado.web.authenticated
	def get(self, errors=None):
		add_panel_config=OrderedDict([
			['FILTER_ADD_MIDI_EVENT', {
				'options': list(self.midi_event_options.keys()),
				'option_labels': self.midi_event_options
			}],
			['FILTER_ADD_TRANSLATED_MIDI_EVENT', {
				'options': list(self.midi_event_options.keys()),
				'option_labels': self.midi_event_options
			}],
			['FILTER_ADD_CC_VALUE', {
				'option_labels': self.midi_cc_labels
			}],
			['FILTER_ADD_TRANSLATED_CC_VALUE', {
				'option_labels': self.midi_cc_labels
			}]
		])

		config=OrderedDict([
			['ZYNTHIAN_PRESET_PRELOAD_NOTEON', {
				'type': 'boolean',
				'title': 'Preset preload on Note-On',
				'value': os.getenv('ZYNTHIAN_PRESET_PRELOAD_NOTEON',"0")
			}],
			['ZYNTHIAN_MIDI_FINE_TUNING', {
				'type': 'select',
				'title': 'MIDI fine tuning (Hz)',
				'value':  os.getenv('ZYNTHIAN_MIDI_FINE_TUNING','440'),
				'options': map(lambda x: str(x).zfill(2), list(range(392, 493)))
			}],
			['ZYNTHIAN_MASTER_MIDI_CHANNEL', {
				'type': 'select',
				'title': 'Master MIDI channel',
				'value': os.getenv('MIDI_MASTER_CHANNEL','16'),
				'options': map(lambda x: str(x).zfill(2), list(range(1, 17)))
			}],
			['ZYNTHIAN_MASTER_MIDI_BANK_CHANGE_CCNUM', {
				'type': 'select',
				'title': 'Master Bank change mode',
				'value': os.getenv('ZYNTHIAN_MASTER_MIDI_BANK_CHANGE_CCNUM',''),
				'options': list(self.program_change_mode_labels.keys()),
				'option_labels': self.program_change_mode_labels,
				'advanced': True
			}],
			['ZYNTHIAN_MASTER_MIDI_CHANGE_TYPE', {
				'type': 'select',
				'title': 'Master change type',
				'value': os.getenv('ZYNTHIAN_MASTER_MIDI_CHANGE_TYPE',''),
				'options': list(self.midi_program_change_presets.keys()),
				'presets': self.midi_program_change_presets
			}],
			['ZYNTHIAN_MASTER_MIDI_PROGRAM_CHANGE_UP', {
				'type': 'text',
				'title': 'Master Program change-up',
				'value': os.getenv('ZYNTHIAN_MASTER_MIDI_PROGRAM_CHANGE_UP',''),
				'advanced': True
			}],
			['ZYNTHIAN_MASTER_MIDI_PROGRAM_CHANGE_DOWN', {
				'type': 'text',
				'title': 'Master Program change-down',
				'value': os.getenv('ZYNTHIAN_MASTER_MIDI_PROGRAM_CHANGE_DOWN',''),
				'advanced': True
			}],
			['ZYNTHIAN_MASTER_MIDI_BANK_CHANGE_UP', {
				'type': 'text',
				'title': 'Master Bank change-up',
				'value': os.getenv('ZYNTHIAN_MASTER_MIDI_BANK_CHANGE_UP',''),
				'advanced': True
			}],
			['ZYNTHIAN_MASTER_MIDI_BANK_CHANGE_DOWN', {
				'type': 'text',
				'title': 'Master Bank change-down',
				'value': os.getenv('ZYNTHIAN_MASTER_MIDI_BANK_CHANGE_DOWN',''),
				'advanced': True
			}],
			['ZYNTHIAN_MASTER_MIDI_EVENT_TRANSLATIONS', {
				'type': 'textarea',
				'title': 'Translate midi events',
				'value': os.getenv('ZYNTHIAN_MASTER_MIDI_EVENT_TRANSLATIONS',""),
				'cols': 50,
				'rows': 5,
				'addButton': 'midi_translation_add',
				'addPanel': 'midi_translation.html',
				'addPanelConfig': add_panel_config,
				'advanced': True
			}]
		])
		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="config_block.html", config=config, title="MIDI", errors=errors)

	def post(self):
		escaped_request_arguments = tornado.escape.recursive_unicode(self.request.arguments)
		if 'FILTER_ADD_COMMAND' in escaped_request_arguments and 'FILTER_ADD_MIDI_EVENT' in escaped_request_arguments:
			self.calculateTranslation(escaped_request_arguments)
		self.request.arguments['ZYNTHIAN_PRESET_PRELOAD_NOTEON'] = self.request.arguments.get('ZYNTHIAN_PRESET_PRELOAD_NOTEON','0')
		errors=self.update_config(escaped_request_arguments)
		self.restart_ui()
		self.get(errors)

	def calculateTranslation(self, escaped_request_arguments):
		if escaped_request_arguments['FILTER_ADD_COMMAND'][0]:
			channels = ''
			if 'FILTER_ADD_CHANNEL' in escaped_request_arguments and escaped_request_arguments['FILTER_ADD_CHANNEL'][0]:
				channels =  'CH#' + ','.join(str(x) for x in escaped_request_arguments['FILTER_ADD_CHANNEL'])
			midiEvent = ''
			if 'FILTER_ADD_MIDI_EVENT' in escaped_request_arguments and escaped_request_arguments['FILTER_ADD_MIDI_EVENT'][0]:
				midiEvent = escaped_request_arguments['FILTER_ADD_MIDI_EVENT'][0]
			ccValue = ''
			if 'FILTER_ADD_CC_VALUE' in escaped_request_arguments and escaped_request_arguments['FILTER_ADD_CC_VALUE'][0]:
				ccValue = '#' +  ','.join(str(x) for x in escaped_request_arguments['FILTER_ADD_CC_VALUE'])
			translatedMidiEvent = ''
			if 'FILTER_ADD_TRANSLATED_MIDI_EVENT' in escaped_request_arguments and escaped_request_arguments['FILTER_ADD_TRANSLATED_MIDI_EVENT'][0]:
				translatedMidiEvent = '=> ' + escaped_request_arguments['FILTER_ADD_TRANSLATED_MIDI_EVENT'][0]
				if 'FILTER_ADD_TRANSLATED_CC_VALUE' in escaped_request_arguments and escaped_request_arguments['FILTER_ADD_TRANSLATED_CC_VALUE'][0]:
					translatedMidiEvent += '#' +  ','.join(str(x) for x in escaped_request_arguments['FILTER_ADD_TRANSLATED_CC_VALUE'])

			newLine = escaped_request_arguments['FILTER_ADD_COMMAND'][0] + ' ' + channels + ' ' + midiEvent + ' ' + ccValue + ' ' + translatedMidiEvent
			logging.info("new line : %s" % (newLine))
			escaped_request_arguments['ZYNTHIAN_MASTER_MIDI_EVENT_TRANSLATIONS'][0] += 	"\n" + newLine

		for filterAddArgument in list(escaped_request_arguments.keys()):
			if filterAddArgument.startswith('FILTER_ADD'):
				del escaped_request_arguments[filterAddArgument]
