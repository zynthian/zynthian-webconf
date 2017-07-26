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
			'PROGRAM_CHANGE_UP': '',
			'PROGRAM_CHANGE_DOWN': ''
		}],
		['Roland', {
			'PROGRAM_CHANGE_UP': '#cc100#cc101',
			'PROGRAM_CHANGE_DOWN': '#cc100#cc101'
		}]
	])

	@tornado.web.authenticated
	def get(self, errors=None):
		config=OrderedDict([
			['MASTER_CHANNEL', {
				'type': 'select',
				'title': 'Master MIDI channel',
				'value': os.getenv('MIDI_MASTER_CHANNEL','16'),
				'options': map(lambda x: str(x).zfill(2), list(range(1, 17)))
			}],
			['PROGRAM_CHANGE_TYPE', {
				'type': 'select',
				'title': 'Program change type',
				'value': os.getenv('PROGRAM_CHANGE_TYPE',''),
				'options': list(self.midi_program_change_presets.keys()),
				'presets': self.midi_program_change_presets
			}],
			['PROGRAM_CHANGE_UP', {
				'type': 'text',
				'title': 'Program change up',
				'value': os.getenv('PROGRAM_CHANGE_UP',''),
				'advanced': True
			}],
			['PROGRAM_CHANGE_DOWN', {
				'type': 'text',
				'title': 'Program change up',
				'value': os.getenv('PROGRAM_CHANGE_DOWN',''),
				'advanced': True
			}],
			['MASTER_TUNING', {
				'type': 'select',
				'title': 'MIDI Master fine tuning (Hz)',
				'value':  os.getenv('MASTER_FINE_TUNING','440'),
				'options': map(lambda x: str(x).zfill(2), list(range(351, 450)))
			}]
		])
		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="config_block.html", config=config, title="MIDI", errors=errors)

	def post(self):
		errors=self.update_config(tornado.escape.recursive_unicode(self.request.arguments))
		self.restart_ui()
		self.get(errors)
