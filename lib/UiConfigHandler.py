import os
import logging
import tornado.web
from collections import OrderedDict
from lib.ZynthianConfigHandler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# UI Configuration
#------------------------------------------------------------------------------

class UiConfigHandler(ZynthianConfigHandler):

	font_families=[
		"Audiowide",
		"Helvetica",
		"Economica",
		"Orbitron",
		"Abel"
	]

	@tornado.web.authenticated
	def get(self, errors=None):
		config=OrderedDict([
			['ZYNTHIAN_UI_FONT_SIZE', {
				'type': 'text',
				'title': 'Size',
				'value': os.environ.get('ZYNTHIAN_UI_FONT_SIZE')
			}],
			['ZYNTHIAN_UI_FONT_FAMILY', {
				'type': 'select',
				'title': 'Family',
				'value': os.environ.get('ZYNTHIAN_UI_FONT_FAMILY'),
				'options': self.font_families,
				'advanced': True
			}],
			['ZYNTHIAN_UI_COLOR_BG', {
				'type': 'text',
				'title': 'Background',
				'value': os.environ.get('ZYNTHIAN_UI_COLOR_BG'),
				'advanced': True
			}],
			['ZYNTHIAN_UI_COLOR_TX', {
				'type': 'text',
				'title': 'Text',
				'value': os.environ.get('ZYNTHIAN_UI_COLOR_TX'),
				'advanced': True
			}],
			['ZYNTHIAN_UI_COLOR_ON', {
				'type': 'text',
				'title': 'Light',
				'value': os.environ.get('ZYNTHIAN_UI_COLOR_ON'),
				'advanced': True
			}],
			['ZYNTHIAN_UI_COLOR_PANEL_BG', {
				'type': 'text',
				'title': 'Panel Background',
				'value': os.environ.get('ZYNTHIAN_UI_COLOR_PANEL_BG'),
				'advanced': True
			}],
			['ZYNTHIAN_UI_ENABLE_CURSOR', {
				'type': 'boolean',
				'title': 'Enable cursor',
				'value': os.environ.get('ZYNTHIAN_UI_ENABLE_CURSOR', '0'),
				'advanced': True
			}]
		])
		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="config_block.html", config=config, title="User Interface", errors=errors)

	def post(self):
		self.request.arguments['ZYNTHIAN_UI_ENABLE_CURSOR'] = self.request.arguments.get('ZYNTHIAN_UI_ENABLE_CURSOR','0')
		errors=self.update_config(tornado.escape.recursive_unicode(self.request.arguments))
		self.restart_ui()
		self.get(errors)
