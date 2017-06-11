import os
import re
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

	soundcard_mixer_controls=OrderedDict([
		['HifiBerry DAC+', ['Digital']],
		['HifiBerry DAC', []],
		['HifiBerry Digi', []],
		['HifiBerry Amp',[]],
		['AudioInjector', []],
		['IQAudio DAC', []],
		['IQAudio DAC+', []],
		['IQAudio Digi', []],
		['PiSound', []],
		['JustBoom DAC', []],
		['JustBoom Digi', []],
		['USB device', []]
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
			}]
		])

		self.getMixerControls(config)

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="config_block.html", config=config, title="Audio", errors=errors)

	def post(self):
		postedConfig = tornado.escape.recursive_unicode(self.request.arguments)
		errors=self.update_config(postedConfig)
		for varname in postedConfig:
			if varname.find('ALSA_VOLUME_')>=0:
				mixerControl = varname[12:].replace('_',' ')
				call("amixer -M set '" + mixerControl + "' Playback " + self.get_argument(varname) + "% unmute", shell=True)
		self.get(errors)

	def getMixerControls(self, config):
		mixerControl = None
		controlName = ''
		playbackChannel = False
		volumePercent = ''
		idx = 0
		for byteLine in check_output("amixer -M", shell=True).splitlines():
			line = byteLine.decode("utf-8")

			if line.find('Simple mixer control')>=0:
				if controlName and playbackChannel:
					self.addMixerControl(config, mixerControl, controlName, volumePercent)
				mixerControl = {'type': 'slider',
					'id': idx,
					'title': '',
					'value': 0,
					'min': 0,
					'max': 100,
					'step': 1,
					'advanced': False}
				controlName = ''
				playbackChannel = False
				volumePercent = ''
				idx += 1
				m = re.match("Simple mixer control '(.*?)'.*", line, re.M | re.I)
				if m:
					controlName = m.group(1)
			elif line.find('Playback channels:')>=0:
					playbackChannel = True
			else:
				m = re.match(".*Playback.*\[(\d*)%\].*", line, re.M | re.I)
				if m:
					volumePercent = m.group(1)
		if controlName and playbackChannel:
			self.addMixerControl(config, mixerControl, controlName, volumePercent)


	def addMixerControl(self, config, mixerControl, controlName, volumePercent):
		validMixer = ''
		if os.environ.get('SOUNDCARD_NAME'):
			validMixer = self.soundcard_mixer_controls[os.environ.get('SOUNDCARD_NAME')]

		realControlName = controlName.replace(' ','_')
		if not validMixer or realControlName in validMixer:
			configKey = 'ALSA_VOLUME_' + realControlName
			mixerControl['title'] = 'ALSA volume ' + controlName
			mixerControl['value'] = volumePercent

			config[configKey] = mixerControl
