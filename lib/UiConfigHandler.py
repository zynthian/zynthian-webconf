import os
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
			['ZYNTHIAN_UI_FONT_FAMILY', {
				'type': 'select',
				'title': 'Family',
				'value': os.environ.get('ZYNTHIAN_UI_FONT_FAMILY'),
				'options': self.font_families
			}],
			['ZYNTHIAN_UI_FONT_SIZE', {
				'type': 'text',
				'title': 'Size',
				'value': os.environ.get('ZYNTHIAN_UI_FONT_SIZE')
			}],
			['ZYNTHIAN_UI_COLOR_BG', {
				'type': 'text',
				'title': 'Background',
				'value': os.environ.get('ZYNTHIAN_UI_COLOR_BG')
			}],
			['ZYNTHIAN_UI_COLOR_TX', {
				'type': 'text',
				'title': 'Text',
				'value': os.environ.get('ZYNTHIAN_UI_COLOR_TX')
			}],
			['ZYNTHIAN_UI_COLOR_ON', {
				'type': 'text',
				'title': 'Light',
				'value': os.environ.get('ZYNTHIAN_UI_COLOR_ON')
			}],
			['ZYNTHIAN_UI_COLOR_PANEL_BG', {
				'type': 'text',
				'title': 'Panel Background',
				'value': os.environ.get('ZYNTHIAN_UI_COLOR_PANEL_BG')
			}]
		])
		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="config_block.html", config=config, title="User Interface", errors=errors)

	def post(self):
		errors=self.update_config(tornado.escape.recursive_unicode(self.request.arguments))
		self.get(errors)
