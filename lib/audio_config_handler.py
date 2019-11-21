# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Audio Configuration Handler
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
from collections import OrderedDict
from subprocess import check_output, call
from lib.zynthian_config_handler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# Audio Configuration
#------------------------------------------------------------------------------

class AudioConfigHandler(ZynthianConfigHandler):

	soundcard_presets=OrderedDict([
		['HifiBerry DAC+ ADC PRO', {
			'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dacplusadcpro',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw'
		}],
		['HifiBerry DAC+ ADC', {
			'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dacplusadc',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw'
		}],
		['HifiBerry DAC+', {
			'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dacplus',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw'
		}],
		['HifiBerry DAC+ light', {
			'SOUNDCARD_CONFIG':'dtoverlay=hifiberry-dac',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw'
		}],
		['HifiBerry DAC+ RTC', {
			'SOUNDCARD_CONFIG':'dtoverlay=hifiberry-dac\n'+
				'dtoverlay=i2c-rtc,ds130',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw'
		}],
		['HifiBerry Digi', {
			'SOUNDCARD_CONFIG':'dtoverlay=hifiberry-digi',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -P -S -r 44100 -p 256 -n 2 -X raw'
		}],
		['HifiBerry Amp', {
			'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-amp',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw'
		}],
		['AudioInjector', {
			'SOUNDCARD_CONFIG': 'dtoverlay=audioinjector-wm8731-audio',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:audioinjectorpi -S -r 44100 -p 256 -n 2 -X raw'
		}],
		['AudioInjector Ultra', {
			'SOUNDCARD_CONFIG': 'dtoverlay=audioinjector-ultra',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:audioinjectorul -r 48000 -p 256 -n 2 -X raw'
		}],
		['IQAudio DAC', {
			'SOUNDCARD_CONFIG': 'dtoverlay=iqaudio-dac',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw'
		}],
		['IQAudio DAC+', {
			'SOUNDCARD_CONFIG': 'dtoverlay=iqaudio-dacplus',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw'
		}],
		['IQAudio Digi', {
			'SOUNDCARD_CONFIG': 'dtoverlay=iqaudio-digi-wm8804-audio',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw'
		}],
		['PiSound', {
			'SOUNDCARD_CONFIG': 'dtoverlay=pisound',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw'
		}],
		['JustBoom DAC', {
			'SOUNDCARD_CONFIG': 'dtoverlay=justboom-dac',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw'
		}],
		['JustBoom Digi', {
			'SOUNDCARD_CONFIG': 'dtoverlay=justboom-digi',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw'
		}],
		['Fe-Pi Audio', {
			'SOUNDCARD_CONFIG': 'dtoverlay=fe-pi-audio',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw'
		}],
		['Generic USB device', {
			'SOUNDCARD_CONFIG': '',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw'
		}],
		['Behringer UCA222 (USB)', {
			'SOUNDCARD_CONFIG': '',
			'JACKD_OPTIONS': '-P 70 -t 2000 -d alsa -d hw:CODEC -r 48000 -p 256 -n 3 -s -S -X raw'
		}],
		['Behringer UMC404HD (USB)', {
			'SOUNDCARD_CONFIG': '',
			'JACKD_OPTIONS': '-P 70 -t 2000 -d alsa -d hw:CARD=U192k -r 48000 -p 256 -n 3 -s -S -X raw'
		}],
		['Steinberg UR22 mkII (USB)', {
			'SOUNDCARD_CONFIG': '',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw'
		}],
		['Edirol UA1-EX (USB)', {
			'SOUNDCARD_CONFIG': '',
			'JACKD_OPTIONS': '-P 70 -t 2000 -d alsa -d hw:UA1EX -r 44100 -p 1024 -n 2 -S -X raw'
		}],
		['Dummy device', {
			'SOUNDCARD_CONFIG': '',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw'
		}],
		['Custom device', {
			'SOUNDCARD_CONFIG': '',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw'
		}]
	])

	soundcard_mixer_controls=OrderedDict([
		['HifiBerry DAC+', ['Digital']],
		['HifiBerry DAC+ ADC', ['Digital','Analogue']],
		['HifiBerry DAC+ light', ['Digital']],
		['HifiBerry DAC+ RTC', ['Digital']],
		['HifiBerry Digi', []],
		['HifiBerry Amp',[]],
		['AudioInjector', ['Master','Capture']],
		['AudioInjector Ultra', ['DAC','PGA']],
		['IQAudio DAC', []],
		['IQAudio DAC+', []],
		['IQAudio Digi', []],
		['PiSound', []],
		['JustBoom DAC', []],
		['JustBoom Digi', []],
		['Fe-Pi Audio', []],
		['USB device', []],
		['Behringer UCA222 (USB)', ['PCM']],
		['Behringer UMC404HD (USB)', ['UMC404HD_192k_Output', 'Mic']],
		['Steinberg UR22 mkII (USB)', ['Clock_Source_41_Validity']],
		['Edirol UA1-EX (USB)', []],
		['Dummy device', []]
	])

	@tornado.web.authenticated
	def get(self, errors=None):

		if os.environ.get('ZYNTHIAN_KIT_VERSION')!='Custom':
			enable_custom_text = " (select Custom kit to enable)"
		else:
			enable_custom_text = ""

		config=OrderedDict([
			['SOUNDCARD_NAME', {
				'type': 'select',
				'title': "Soundcard{}".format(enable_custom_text),
				'value': os.environ.get('SOUNDCARD_NAME'),
				'options': list(self.soundcard_presets.keys()),
				'presets': self.soundcard_presets,
				'disabled': enable_custom_text!=""
			}],
			['SOUNDCARD_CONFIG', {
				'type': 'textarea',
				'title': "Config{}".format(enable_custom_text),
				'cols': 50,
				'rows': 4,
				'value': os.environ.get('SOUNDCARD_CONFIG'),
				'advanced': True,
				'disabled': enable_custom_text!=""
			}],
			['JACKD_OPTIONS', {
				'type': 'text',
				'title': "Jackd Options{}".format(enable_custom_text),
				'value': os.environ.get('JACKD_OPTIONS',"-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw"),
				'advanced': True,
				'disabled': enable_custom_text!=""
			}],
			['ZYNTHIAN_AUBIONOTES_OPTIONS', {
				'type': 'text',
				'title': "Aubionotes Options",
				'value': os.environ.get('ZYNTHIAN_AUBIONOTES_OPTIONS',"-O complex -t 0.5 -s -88  -p yinfft -l 0.5"),
				'advanced': True
			}],
			['ZYNTHIAN_LIMIT_USB_SPEED', {
				'type': 'boolean',
				'title': "Limit USB speed to 12Mb/s",
				'value': os.environ.get('ZYNTHIAN_LIMIT_USB_SPEED','0'),
				'advanced': True
			}]
		])

		self.get_mixer_controls(config)

		super().get("Audio", config, errors)


	@tornado.web.authenticated
	def post(self):
		self.request.arguments['ZYNTHIAN_LIMIT_USB_SPEED'] = self.request.arguments.get('ZYNTHIAN_LIMIT_USB_SPEED', '0')
		postedConfig = tornado.escape.recursive_unicode(self.request.arguments)
		errors=self.update_config(postedConfig)

		for varname in postedConfig:
			if varname.find('ALSA_VOLUME_')>=0:
				channelName = varname[12:]
				channelType = ''
				mixerControl = ''
				if channelName.find('Playback')>=0:
					channelType = 'Playback'
					mixerControl = channelName[8:].replace('_',' ')
				else:
					channelType = 'Capture'
					mixerControl = channelName[7:].replace('_',' ')

				try:
					amixer_command = "amixer -M set '" + mixerControl + "' " + channelType + " " + self.get_argument(varname) + "% unmute"
					logging.info(amixer_command)
					call(amixer_command, shell=True)
				except Exception as err:
					logging.error("Alsa Mixer => {}".format(err))
					errors["ALSAMIXER_{}".format(varname)] = str(err)

		self.reboot_flag = True
		self.get(errors)


	def get_mixer_controls(self, config):
		mixerControl = None
		controlName = ''
		is_capture = False
		is_playback = False

		volumePercent = ''
		idx = 0
		try:
			for byteLine in check_output("amixer -M", shell=True).splitlines():
				line = byteLine.decode("utf-8")

				if line.find('Simple mixer control')>=0:
					if controlName and (is_capture or is_playback):
						if is_capture:
							self.add_mixer_control(config, mixerControl, controlName, volumePercent, 'Capture')
						else:
							self.add_mixer_control(config, mixerControl, controlName, volumePercent, 'Playback')
					mixerControl = {'type': 'slider',
						'id': idx,
						'title': '',
						'value': 0,
						'min': 0,
						'max': 100,
						'step': 1,
						'advanced': False}
					controlName = ''
					is_capture = False
					is_playback = False


					volumePercent = ''
					idx += 1
					m = re.match("Simple mixer control '(.*?)'.*", line, re.M | re.I)
					if m:
						controlName = m.group(1).strip()
				elif line.find('Capture channels:')>=0:
						is_capture = True
				elif line.find('Playback channels:')>=0:
						is_playback = True
				else:
					m = re.match(".*(Playback|Capture).*\[(\d*)%\].*", line, re.M | re.I)
					if m:
						volumePercent = m.group(2)
						if m.group(1) == 'Capture':
							is_capture = True
						else:
							is_playback = True
					else:
						m = re.match(".*\[(\d*)%\].*", line, re.M | re.I)
						if m:
							volumePercent = m.group(1)

			if controlName and (is_playback or is_capture):
				if is_playback:
					self.add_mixer_control(config, mixerControl, controlName, volumePercent, 'Playback')
				else:
					self.add_mixer_control(config, mixerControl, controlName, volumePercent, 'Capture')

		except Exception as err:
			logging.error(format(err))


	def add_mixer_control(self, config, mixerControl, controlName, volumePercent, channelType):
		validMixer = ''
		if os.environ.get('SOUNDCARD_NAME'):
			validMixer = self.soundcard_mixer_controls[os.environ.get('SOUNDCARD_NAME')]

		realControlName = controlName.replace(' ','_')
		if not validMixer or realControlName in validMixer:
			configKey = 'ALSA_VOLUME_' + channelType + '_' + realControlName
			mixerControl['title'] = 'ALSA volume ' + controlName
			mixerControl['value'] = volumePercent

			config[configKey] = mixerControl

