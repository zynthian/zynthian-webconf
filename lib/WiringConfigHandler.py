import os
import tornado.web
from collections import OrderedDict
from lib.ZynthianConfigHandler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# Wiring Configuration
#------------------------------------------------------------------------------

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
				'title': 'Encoder A GPIO-pins',
				'value': os.environ.get('ZYNTHIAN_WIRING_ENCODER_A'),
				'advanced': True
			}],
			['ZYNTHIAN_WIRING_ENCODER_B', {
				'type': 'text',
				'title': 'Encoder B GPIO-pins',
				'value': os.environ.get('ZYNTHIAN_WIRING_ENCODER_B'),
				'advanced': True
			}],
			['ZYNTHIAN_WIRING_SWITCHES', {
				'type': 'text',
				'title': 'Switch GPIO-pins',
				'value': os.environ.get('ZYNTHIAN_WIRING_SWITCHES'),
				'advanced': True
			}]
		])
		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="config_block.html", config=config, title="Wiring", errors=errors)

	def post(self):
		errors=self.update_config(tornado.escape.recursive_unicode(self.request.arguments))
		errors=self.get()
