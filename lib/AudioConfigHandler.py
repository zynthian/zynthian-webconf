import os
import tornado.web
import logging
from collections import OrderedDict
from lib.ZynthianConfigHandler import ZynthianConfigHandler
from subprocess import check_output
from subprocess import call

#------------------------------------------------------------------------------
# Audio Configuration
#------------------------------------------------------------------------------

class AudioConfigHandler(ZynthianConfigHandler):
	alsaMasterItem = "Digital"

	soundcard_presets=OrderedDict([
		['HifiBerry DAC+', {
			'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dacplus'
		}],
		['HifiBerry DAC', {
			'SOUNDCARD_CONFIG':'dtoverlay=hifiberry-dac'
		}],
		['HifiBerry Digi', {
			'SOUNDCARD_CONFIG':'dtoverlay=hifiberry-digi'
		}],
		['HifiBerry Amp', {
			'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-amp'
		}],
		['AudioInjector', {
			'SOUNDCARD_CONFIG': 'dtoverlay=audioinjector-wm8731-audio'
		}],
		['IQAudio DAC', {
			'SOUNDCARD_CONFIG': 'dtoverlay=iqaudio-dac'
		}],
		['IQAudio DAC+', {
			'SOUNDCARD_CONFIG': 'dtoverlay=iqaudio-dacplus'
		}],
		['IQAudio Digi', {
			'SOUNDCARD_CONFIG': 'dtoverlay=iqaudio-digi-wm8804-audio'
		}],
		['PiSound', {
			'SOUNDCARD_CONFIG': 'dtoverlay=pisound'
		}],
		['JustBoom DAC', {
			'SOUNDCARD_CONFIG': 'dtoverlay=justboom-dac'
		}],
		['JustBoom Digi', {
			'SOUNDCARD_CONFIG': 'dtoverlay=justboom-digi'
		}],
		['USB device', {
			'SOUNDCARD_CONFIG': ''
		}]
	])

	@tornado.web.authenticated
	def get(self, errors=None):
		config=OrderedDict([
			['SOUNDCARD_NAME', {
				'type': 'select',
				'title': 'Soundcard',
				'value': os.environ.get('SOUNDCARD_NAME'),
				'options': list(self.soundcard_presets.keys()),
				'presets': self.soundcard_presets
			}],
			['SOUNDCARD_CONFIG', {
				'type': 'textarea',
				'title': 'Config',
				'cols': 50,
				'rows': 4,
				'value': os.environ.get('SOUNDCARD_CONFIG'),
				'advanced': True
			}],
			['JACKD_OPTIONS', {
				'type': 'text',
				'title': 'Jackd Options',
				'value': os.environ.get('JACKD_OPTIONS'),
				'advanced': True
			}],
			['ALSA_MASTER_VOLUME', {
				'type': 'slider',
				'title': 'ALSA master volume',
				'value': self.getAlsaMasterVolume(),
				'min': 0,
				'max': 100,
				'step': 1,
				'advanced': False
			}]
		])
		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="config_block.html", config=config, title="Audio", errors=errors)

	def post(self):
		errors=self.update_config(tornado.escape.recursive_unicode(self.request.arguments))
		call("amixer -M set '" + AudioConfigHandler.alsaMasterItem + "' Playback " + self.get_argument('ALSA_MASTER_VOLUME') + "% unmute", shell=True)
		self.get(errors)


 	def getAlsaMasterVolume(self):
        cmd = "amixer -M get '" + AudioConfigHandler.alsaMasterItem + "' | grep 'Playback.*\\[.*\\].*' | sed 's/.*\\[\\(.*\\)%\\].*/\\1/' | head -1"
        logging.info(cmd)
        vol = check_output(cmd, shell=True)
        logging.info(vol)
        return vol
