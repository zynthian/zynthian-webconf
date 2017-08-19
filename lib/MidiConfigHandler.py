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
			'ZYNTHIAN_MASTER_MIDI_PROGRAM_CHANGE_UP': 'PC 127',
			'ZYNTHIAN_MASTER_MIDI_PROGRAM_CHANGE_DOWN': 'PC 000',
			'ZYNTHIAN_MASTER_MIDI_BANK_CHANGE_UP': 'CC 000 127',
			'ZYNTHIAN_MASTER_MIDI_BANK_CHANGE_DOWN': 'CC 000 000'

		}]
	])

	@tornado.web.authenticated
	def get(self, errors=None):
		config=OrderedDict([
			['ZYNTHIAN_MASTER_MIDI_CHANNEL', {
				'type': 'select',
				'title': 'Master MIDI channel',
				'value': os.getenv('MIDI_MASTER_CHANNEL','16'),
				'options': map(lambda x: str(x).zfill(2), list(range(1, 17)))
			}],
			['ZYNTHIAN_MIDI_FINE_TUNING', {
				'type': 'select',
				'title': 'MIDI Master fine tuning (Hz)',
				'value':  os.getenv('ZYNTHIAN_MIDI_FINE_TUNING','440'),
				'options': map(lambda x: str(x).zfill(2), list(range(351, 450)))
			}],
			['ZYNTHIAN_MASTER_MIDI_PROGRAM_CHANGE_TYPE', {
				'type': 'select',
				'title': 'Program change type',
				'value': os.getenv('ZYNTHIAN_MASTER_MIDI_PROGRAM_CHANGE_TYPE',''),
				'options': list(self.midi_program_change_presets.keys()),
				'presets': self.midi_program_change_presets
			}],
			['ZYNTHIAN_MASTER_MIDI_PROGRAM_CHANGE_UP', {
				'type': 'text',
				'title': 'Program change up',
				'value': os.getenv('ZYNTHIAN_MASTER_MIDI_PROGRAM_CHANGE_UP',''),
				'advanced': True
			}],
			['ZYNTHIAN_MASTER_MIDI_PROGRAM_CHANGE_DOWN', {
				'type': 'text',
				'title': 'Program change down',
				'value': os.getenv('ZYNTHIAN_MASTER_MIDI_PROGRAM_CHANGE_DOWN',''),
				'advanced': True
			}],
			['ZYNTHIAN_MASTER_MIDI_BANK_CHANGE_UP', {
				'type': 'text',
				'title': 'Bank change up',
				'value': os.getenv('ZYNTHIAN_MASTER_MIDI_BANK_CHANGE_UP',''),
				'advanced': True
			}],
			['ZYNTHIAN_MASTER_MIDI_BANK_CHANGE_DOWN', {
				'type': 'text',
				'title': 'Bank change down',
				'value': os.getenv('ZYNTHIAN_MASTER_MIDI_BANK_CHANGE_DOWN',''),
				'advanced': True
			}],
			['ZYNTHIAN_PRESET_PRELOAD_NOTEON', {
				'type': 'boolean',
				'title': 'Preset preload on  Note-On',
				'value': os.getenv('ZYNTHIAN_PRESET_PRELOAD_NOTEON',"0")
			}]
		])
		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="config_block.html", config=config, title="MIDI", errors=errors)

	def post(self):
		self.request.arguments['ZYNTHIAN_PRESET_PRELOAD_NOTEON'] = self.request.arguments.get('ZYNTHIAN_PRESET_PRELOAD_NOTEON','0')
		errors=self.update_config(tornado.escape.recursive_unicode(self.request.arguments))
		self.restart_ui()
		self.get(errors)
