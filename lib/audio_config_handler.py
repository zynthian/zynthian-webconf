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
from zyngine.zynthian_engine_mixer import *

#------------------------------------------------------------------------------
# Audio Configuration
#------------------------------------------------------------------------------

class AudioConfigHandler(ZynthianConfigHandler):

	soundcard_presets=OrderedDict([
		['HifiBerry DAC+ ADC PRO', {
			'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dacplusadcpro,slave',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': 'Digital,ADC,ADC Left Input,ADC Right Input'
		}],
		['HifiBerry DAC+ ADC', {
			'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dacplusadc',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': 'Digital,Analogue'
		}],
		['HifiBerry DAC+', {
			'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dacplus',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': 'Digital'
		}],
		['HifiBerry DAC+ light', {
			'SOUNDCARD_CONFIG':'dtoverlay=hifiberry-dac',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': 'Digital'
		}],
		['HifiBerry DAC+ RTC', {
			'SOUNDCARD_CONFIG':'dtoverlay=hifiberry-dac\ndtoverlay=i2c-rtc,ds130',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': 'Digital'
		}],
		['HifiBerry Digi', {
			'SOUNDCARD_CONFIG':'dtoverlay=hifiberry-digi',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -P -S -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': ''
		}],
		['HifiBerry Amp', {
			'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-amp',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': ''
		}],
		['AudioInjector', {
			'SOUNDCARD_CONFIG': 'dtoverlay=audioinjector-wm8731-audio',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:audioinjectorpi -S -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': 'Master,Capture'
		}],
		['AudioInjector Ultra', {
			'SOUNDCARD_CONFIG': 'dtoverlay=audioinjector-ultra',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:audioinjectorul -r 48000 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': 'DAC,PGA'
		}],
		['IQAudio DAC', {
			'SOUNDCARD_CONFIG': 'dtoverlay=iqaudio-dac',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': ''
		}],
		['IQAudio DAC+', {
			'SOUNDCARD_CONFIG': 'dtoverlay=iqaudio-dacplus',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': ''
		}],
		['IQAudio Digi', {
			'SOUNDCARD_CONFIG': 'dtoverlay=iqaudio-digi-wm8804-audio',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': ''
		}],
		['PiSound', {
			'SOUNDCARD_CONFIG': 'dtoverlay=pisound',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': ''
		}],
		['JustBoom DAC', {
			'SOUNDCARD_CONFIG': 'dtoverlay=justboom-dac',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': ''
		}],
		['JustBoom Digi', {
			'SOUNDCARD_CONFIG': 'dtoverlay=justboom-digi',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': ''
		}],
		['Fe-Pi Audio', {
			'SOUNDCARD_CONFIG': 'dtoverlay=fe-pi-audio',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': ''
		}],
		['Generic USB device', {
			'SOUNDCARD_CONFIG': '',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': ''
		}],
		['Behringer UCA222 (USB)', {
			'SOUNDCARD_CONFIG': '',
			'JACKD_OPTIONS': '-P 70 -t 2000 -d alsa -d hw:CODEC -r 48000 -p 256 -n 3 -s -S -X raw',
			'SOUNDCARD_MIXER': 'PCM'
		}],
		['Behringer UMC404HD (USB)', {
			'SOUNDCARD_CONFIG': '',
			'JACKD_OPTIONS': '-P 70 -t 2000 -d alsa -d hw:U192k -r 48000 -p 256 -n 3 -s -S -X raw',
			'SOUNDCARD_MIXER': 'UMC404HD_192k_Output,Mic'
		}],
		['Steinberg UR22 mkII (USB)', {
			'SOUNDCARD_CONFIG': '',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': 'Clock_Source_41_Validity'
		}],
		['Edirol UA1-EX (USB)', {
			'SOUNDCARD_CONFIG': '',
			'JACKD_OPTIONS': '-P 70 -t 2000 -d alsa -d hw:UA1EX -r 44100 -p 1024 -n 2 -S -X raw',
			'SOUNDCARD_MIXER': ''
		}],
		['RBPi On-Board Analog Audio', {
			'SOUNDCARD_CONFIG': 'dtparam=audio=on\naudio_pwm_mode=2',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:ALSA -r 44100 -p 512 -n 3 -X raw',
			'SOUNDCARD_MIXER': 'PCM'
		}],
		['Dummy device', {
			'SOUNDCARD_CONFIG': '',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': ''
		}],
		['Custom device', {
			'SOUNDCARD_CONFIG': '',
			'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw',
			'SOUNDCARD_MIXER': ''
		}]
	])

	@tornado.web.authenticated
	def get(self, errors=None):

		if os.environ.get('ZYNTHIAN_KIT_VERSION')!='Custom':
			enable_custom_text = " (select Custom kit to enable)"
		else:
			enable_custom_text = ""

		zc_config=OrderedDict([
			['ZCONTROLLERS',self.get_controllers()]
		])

		logging.info(zc_config)

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
			}],
			['SOUNDCARD_MIXER', {
				'type': 'textarea',
				'title': "Mixer Controls{}".format(enable_custom_text),
				'value': os.environ.get('SOUNDCARD_MIXER'),
				'cols': 50,
				'rows': 3,
				'addButton': 'display_zcontroller_panel',
				'addPanel': 'zcontroller.html',
				'addPanelConfig': zc_config,
				'advanced': True
			}]
		])

		super().get("Audio", config, errors)

	@tornado.web.authenticated
	def post(self):
		self.request.arguments['ZYNTHIAN_LIMIT_USB_SPEED'] = self.request.arguments.get('ZYNTHIAN_LIMIT_USB_SPEED', '0')
		postedConfig = tornado.escape.recursive_unicode(self.request.arguments)
		for k in list(postedConfig):
			if k.startswith('ZYNTHIAN_CONTROLLER'):
				del postedConfig[k]

		errors=self.update_config(postedConfig)
		self.reboot_flag = True
		self.get(errors)

	def get_device_name(self):
		try:
			jack_opts=os.environ.get('JACKD_OPTIONS')
			res = re.compile(r" hw:([^\s]+) ").search(jack_opts)
			return res.group(1)
		except:
			return "0"

	def get_controllers(self):
		try:
			zynthian_engine_mixer.init_zynapi_instance()
			return zynthian_engine_mixer.zynapi_get_controllers("*")
		except Exception as err:
			logging.error(err)
			return []


