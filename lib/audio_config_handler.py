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
import copy
import logging
import tornado.web
from collections import OrderedDict
from subprocess import check_output, call
from lib.zynthian_config_handler import ZynthianConfigHandler
from zyngine.zynthian_engine_mixer import *

#------------------------------------------------------------------------------
# Soundcard Presets
#------------------------------------------------------------------------------

soundcard_presets = OrderedDict([
	['HifiBerry DAC+ ADC PRO', {
		'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dacplusadcpro',
		'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw',
		'SOUNDCARD_MIXER': 'Digital Left,ADC Left,Digital Right,ADC Right,ADC Left Input,ADC Right Input'
	}],
	['HifiBerry DAC+ ADC', {
		'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dacplusadc',
		'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw',
		'SOUNDCARD_MIXER': 'Digital Left,Digital Right'
	}],
	['HifiBerry DAC+', {
		'SOUNDCARD_CONFIG': 'dtoverlay=hifiberry-dacplus',
		'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw',
		'SOUNDCARD_MIXER': 'Digital Left,Digital Right'
	}],
	['HifiBerry DAC+ light', {
		'SOUNDCARD_CONFIG':'dtoverlay=hifiberry-dac',
		'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw',
		'SOUNDCARD_MIXER': 'Digital Left,Digital Right'
	}],
	['HifiBerry DAC+ RTC', {
		'SOUNDCARD_CONFIG':'dtoverlay=hifiberry-dac\ndtoverlay=i2c-rtc,ds130',
		'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:sndrpihifiberry -S -r 44100 -p 256 -n 2 -X raw',
		'SOUNDCARD_MIXER': 'Digital Left,Digital Right'
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
		'SOUNDCARD_MIXER': 'Master Left,Capture Left,Master Right,Capture Right'
	}],
	['AudioInjector Isolated', {
		'SOUNDCARD_CONFIG': 'dtoverlay=audioinjector-isolated-soundcard',
		'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:audioinjectoris -r 48000 -p 256 -n 2 -X raw',
		'SOUNDCARD_MIXER': 'Master Left,Master Right'
        }],
	['AudioInjector Ultra', {
		'SOUNDCARD_CONFIG': 'dtoverlay=audioinjector-ultra',
		'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:audioinjectorul -r 48000 -p 256 -n 2 -X raw',
		'SOUNDCARD_MIXER': 'DAC Left,DAC Right,PGA'
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
		'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:pisound -r 44100 -p 256 -n 2 -X raw',
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
	['Behringer UCA222', {
		'SOUNDCARD_CONFIG': '',
		'JACKD_OPTIONS': '-P 70 -t 2000 -d alsa -d hw:CODEC -r 48000 -p 256 -n 3 -s -S -X raw',
		'SOUNDCARD_MIXER': 'PCM'
	}],
	['Behringer UMC404HD', {
		'SOUNDCARD_CONFIG': '',
		'JACKD_OPTIONS': '-P 70 -t 2000 -d alsa -d hw:U192k -r 48000 -p 256 -n 3 -s -S -X raw',
		'SOUNDCARD_MIXER': 'UMC404HD_192k_Output,Mic'
	}],
	['Behringer UMC1820', {
		'SOUNDCARD_CONFIG': '',
		'JACKD_OPTIONS': '-P 70 -t 2000 -d alsa -d hw:UMC1820 -r 44100 -p 256 -n 2 -s -S -X raw',
		'SOUNDCARD_MIXER': 'UMC1820 Output'
	}],
	['Behringer X18XR18', {
		'SOUNDCARD_CONFIG': '',
		'JACKD_OPTIONS': '-P 70 -t 2000 -d alsa -d hw:X18XR18 -r 48000 -p 256 -n 2 -s -S -X raw',
		'SOUNDCARD_MIXER': ''
	}],
	['Steinberg UR22 MKII', {
		'SOUNDCARD_CONFIG': '',
		'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:UR22 -r 44100 -p 256 -n 2 -X raw',
		'SOUNDCARD_MIXER': 'Clock_Source_41_Validity'
	}],
	['LogicLink UA0099', {
		'SOUNDCARD_CONFIG': '',
		'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:ICUSBAUDIO7D -r 44100 -p 256 -n 2 -X raw',
		'SOUNDCARD_MIXER': ''
	}],
	['Edirol UA1-EX', {
		'SOUNDCARD_CONFIG': '',
		'JACKD_OPTIONS': '-P 70 -t 2000 -d alsa -d hw:UA1EX -r 44100 -p 1024 -n 2 -S -X raw',
		'SOUNDCARD_MIXER': ''
	}],
	['Yeti Microphone', {
		'SOUNDCARD_CONFIG': '',
		'JACKD_OPTIONS': '-t 2000 -s -d alsa -d hw:Microphone -r 48000 -p 256 -n 2 -X raw',
		'SOUNDCARD_MIXER': 'Speaker Left,Mic Left,Speaker Right,Mic Right'
	}],
	['RBPi Headphones', {
		'SOUNDCARD_CONFIG': 'dtparam=audio=on\naudio_pwm_mode=2',
		'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:#DEVNAME# -r 44100 -p 512 -n 3 -X raw',
		'SOUNDCARD_MIXER': 'Headphone Left,Headphone Right'
	}],
	['RBPi HDMI', {
		'SOUNDCARD_CONFIG': 'dtparam=audio=on',
		'JACKD_OPTIONS': '-P 70 -t 2000 -s -d alsa -d hw:#DEVNAME# -r 44100 -p 512 -n 2 -X raw',
		'SOUNDCARD_MIXER': 'HDMI Left,HDMI Right'
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

try:
	zynthian_engine_mixer.init_zynapi_instance()
	rbpi_device_name = zynthian_engine_mixer.zynapi_get_rbpi_device_name()
	logging.info("RBPi Device Name: '{}'".format(rbpi_device_name))
except Exception as err:
	rbpi_device_name = None
	logging.error(err)

if rbpi_device_name=="Headphones":
	soundcard_presets['RBPi Headphones']['JACKD_OPTIONS'] = soundcard_presets['RBPi Headphones']['JACKD_OPTIONS'].replace("#DEVNAME#","Headphones")
	soundcard_presets['RBPi HDMI']['JACKD_OPTIONS'] = soundcard_presets['RBPi HDMI']['JACKD_OPTIONS'].replace("#DEVNAME#","b1")
elif rbpi_device_name=="ALSA":
	soundcard_presets['RBPi Headphones']['JACKD_OPTIONS'] = soundcard_presets['RBPi Headphones']['JACKD_OPTIONS'].replace("#DEVNAME#","ALSA")
	soundcard_presets['RBPi HDMI']['JACKD_OPTIONS'] = soundcard_presets['RBPi HDMI']['JACKD_OPTIONS'].replace("#DEVNAME#","ALSA")
else:
	del soundcard_presets['RBPi Headphones']
	del soundcard_presets['RBPi HDMI']

#------------------------------------------------------------------------------
# Audio Configuration Class
#------------------------------------------------------------------------------

class AudioConfigHandler(ZynthianConfigHandler):

	zctrls = None

	@tornado.web.authenticated
	def get(self, errors=None):

		zc_config = OrderedDict([
			['ZCONTROLLERS', AudioConfigHandler.get_controllers()]
		])
		logging.info(zc_config)

		config=OrderedDict()

		if os.environ.get('ZYNTHIAN_KIT_VERSION')!='Custom':
			custom_options_disabled = True
			config['ZYNTHIAN_MESSAGE'] = {
				'type': 'html',
				'content': "<div class='alert alert-warning'>Some config options are disabled. You may want to <a href='/hw-kit'>choose Custom Kit</a> for enabling all options.</div>"
			}
		else:
			custom_options_disabled = False

		scpresets = copy.copy(soundcard_presets)
		if os.environ.get('ZYNTHIAN_DISABLE_RBPI_AUDIO','0')=='1':
			try:
				del scpresets['RBPi Headphones']
				del scpresets['RBPi HDMI']
			except:
				pass

		config['SOUNDCARD_NAME'] = {
			'type': 'select',
			'title': "Soundcard",
			'value': os.environ.get('SOUNDCARD_NAME'),
			'options': list(scpresets.keys()),
			'presets': scpresets,
			'disabled': custom_options_disabled,
			'refresh_on_change': True
		}
		config['SOUNDCARD_CONFIG'] = {
			'type': 'textarea',
			'title': "Driver Config",
			'cols': 50,
			'rows': 4,
			'value': os.environ.get('SOUNDCARD_CONFIG'),
			'advanced': True,
			'disabled': custom_options_disabled
		}
		config['JACKD_OPTIONS'] = {
			'type': 'text',
			'title': "Jackd Options",
			'value': os.environ.get('JACKD_OPTIONS',"-P 70 -t 2000 -s -d alsa -d hw:0 -r 44100 -p 256 -n 2 -X raw"),
			'advanced': True,
			'disabled': custom_options_disabled
		}
		config['ZYNTHIAN_AUBIONOTES_OPTIONS'] = {
			'type': 'text',
			'title': "Aubionotes Options",
			'value': os.environ.get('ZYNTHIAN_AUBIONOTES_OPTIONS',"-O complex -t 0.5 -s -88  -p yinfft -l 0.5"),
			'advanced': True
		}
		config['ZYNTHIAN_DISABLE_RBPI_AUDIO'] = {
			'type': 'boolean',
			'title': "Disable RBPi Audio",
			'value': os.environ.get('ZYNTHIAN_DISABLE_RBPI_AUDIO','0'),
			'advanced': True,
			'refresh_on_change': True
		}
		config['ZYNTHIAN_DISABLE_OTG'] = {
			'type': 'boolean',
			'title': "Disable OTG",
			'value': os.environ.get('ZYNTHIAN_DISABLE_OTG','0'),
			'advanced': True
		}
		config['ZYNTHIAN_LIMIT_USB_SPEED'] = {
			'type': 'boolean',
			'title': "Limit USB speed to 12Mb/s",
			'value': os.environ.get('ZYNTHIAN_LIMIT_USB_SPEED','0'),
			'advanced': True
		}
		config['SOUNDCARD_MIXER'] = {
			'type': 'textarea',
			'title': "Mixer Controls",
			'value': os.environ.get('SOUNDCARD_MIXER'),
			'cols': 50,
			'rows': 3,
			'addButton': 'display_zcontroller_panel',
			'addPanel': 'zcontroller.html',
			'addPanelConfig': zc_config,
			'advanced': True
		}
		config['JAMULUS_OPTIONS'] = {
			'type': 'text',
			'title': "Jamulus Options",
			'value': os.environ.get('JAMULUS_OPTIONS',"-n -i /root/Jamulus.ini -c your_favorite_jamulus_address"),
			'advanced': True
		}

		if os.environ.get('ZYNTHIAN_DISABLE_RBPI_AUDIO','0')=='0' and os.environ.get('SOUNDCARD_NAME')!="RBPi Headphones":
			config['ZYNTHIAN_RBPI_HEADPHONES'] = {
				'type': 'boolean',
				'title': "RBPi Headphones",
				'value': os.environ.get('ZYNTHIAN_RBPI_HEADPHONES','0')
			}

		super().get("Audio", config, errors)


	@tornado.web.authenticated
	def post(self):
		command = self.get_argument('_command', '')
		logging.info("COMMAND = {}".format(command))
		if command=='REFRESH':
			errors = None
			self.config_env(tornado.escape.recursive_unicode(self.request.arguments))

		else:
			self.request.arguments['ZYNTHIAN_LIMIT_USB_SPEED'] = self.request.arguments.get('ZYNTHIAN_LIMIT_USB_SPEED', '0')
			self.request.arguments['ZYNTHIAN_DISABLE_RBPI_AUDIO'] = self.request.arguments.get('ZYNTHIAN_DISABLE_RBPI_AUDIO', '0')
			self.request.arguments['ZYNTHIAN_DISABLE_OTG'] = self.request.arguments.get('ZYNTHIAN_DISABLE_OTG', '0')
			self.request.arguments['ZYNTHIAN_RBPI_HEADPHONES'] = self.request.arguments.get('ZYNTHIAN_RBPI_HEADPHONES', '0')

			try:
				previousSoundcard = os.environ.get('SOUNDCARD_NAME')
				currentSoundcard = self.get_argument('SOUNDCARD_NAME')
				if currentSoundcard.startswith('AudioInjector') and currentSoundcard!=previousSoundcard:
					self.persist_update_sys_flag()
				if currentSoundcard=="RBPi Headphones":
					self.request.arguments['ZYNTHIAN_RBPI_HEADPHONES']=['0']
			except:
				pass

			postedConfig = tornado.escape.recursive_unicode(self.request.arguments)
			for k in list(postedConfig):
				if k.startswith('ZYNTHIAN_CONTROLLER'):
					del postedConfig[k]

			errors=self.update_config(postedConfig)
			self.reboot_flag = True

		self.get(errors)


	def get_device_name(self):
		try:
			zynthian_engine_mixer.init_zynapi_instance()
			device_name = zynthian_engine_mixer.zynapi_get_device_name()
		except Exception as err:
			device_name = 0
			logging.error(err)

		return device_name


	@classmethod
	def get_controllers(cls):
		try:
			zynthian_engine_mixer.init_zynapi_instance()
			AudioConfigHandler.zctrls = zynthian_engine_mixer.zynapi_get_controllers("*")
			return AudioConfigHandler.zctrls
		except Exception as err:
			logging.error(err)
			return []


