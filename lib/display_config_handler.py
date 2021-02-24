# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Display Configuration Handler
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
import logging
import tornado.web
from subprocess import check_output
from collections import OrderedDict
from lib.zynthian_config_handler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# Display Configuration
#------------------------------------------------------------------------------

class DisplayConfigHandler(ZynthianConfigHandler):

	display_presets=OrderedDict([
		['ZynScreen 3.5 (v1)', {
			'DISPLAY_CONFIG': 'dtoverlay=piscreen2r-notouch,rotate=270\n'+
				'dtoverlay=ads7846,speed=2000000,cs=1,penirq=17,penirq_pull=2,swapxy=1,xohms=100,pmax=255',
			'DISPLAY_WIDTH': '480',
			'DISPLAY_HEIGHT': '320',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['PiScreen 3.5 (v2)', {
			'DISPLAY_CONFIG': 'dtoverlay=piscreen2r-notouch,rotate=270\n'+
				'dtoverlay=ads7846,speed=2000000,cs=1,penirq=17,penirq_pull=2,swapxy=1,xohms=100,pmax=255',
			'DISPLAY_WIDTH': '480',
			'DISPLAY_HEIGHT': '320',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['PiScreen 3.5 (v1)', {
			'DISPLAY_CONFIG': 'dtoverlay=piscreen,speed=16000000,rotate=90',
			'DISPLAY_WIDTH': '480',
			'DISPLAY_HEIGHT': '320',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['PiTFT 2.8 Resistive', {
			'DISPLAY_CONFIG': 'dtoverlay=pitft28-resistive,rotate=90,speed=32000000,fps=20',
			'DISPLAY_WIDTH': '320',
			'DISPLAY_HEIGHT': '240',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['PiTFT 2.8 Capacitive', {
			'DISPLAY_CONFIG': 'dtoverlay=pitft28-capacitive,rotate=90,speed=32000000,fps=20',
			'DISPLAY_WIDTH': '320',
			'DISPLAY_HEIGHT': '240',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['PiTFT 3.5 Resistive', {
			'DISPLAY_CONFIG': 'dtoverlay=pitft35-resistive,rotate=90,speed=32000000,fps=20',
			'DISPLAY_WIDTH': '480',
			'DISPLAY_HEIGHT': '320',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['RPi-Display 2.8', {
			'DISPLAY_CONFIG': 'dtoverlay=rpi-display,speed=32000000,rotate=270',
			'DISPLAY_WIDTH': '320',
			'DISPLAY_HEIGHT': '240',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['WaveShare 3.2B', {
			'DISPLAY_CONFIG':
				'dtoverlay=waveshare32b:rotate=270,swapxy=1\n'+
				'#dtoverlay=ads7846,cs=1,penirq=17,penirq_pull=2,speed=1000000,keep_vref_on=1,swapxy=0,pmax=255,xohms=60,xmin=200,xmax=3900,ymin=200,ymax=3900\n',
			'DISPLAY_WIDTH': '320',
			'DISPLAY_HEIGHT': '240',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['WaveShare 3.2C', {
			'DISPLAY_CONFIG':
				'dtoverlay=waveshare32c:rotate=270,swapxy=1\n'+
				'#dtoverlay=ads7846,cs=1,penirq=17,penirq_pull=2,speed=1000000,keep_vref_on=1,swapxy=0,pmax=255,xohms=60,xmin=200,xmax=3900,ymin=200,ymax=3900\n',
			'DISPLAY_WIDTH': '320',
			'DISPLAY_HEIGHT': '240',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['WaveShare 3.5A', {
			'DISPLAY_CONFIG':
				'dtoverlay=waveshare35a:rotate=270,swapxy=1\n'+
				'#dtoverlay=ads7846,cs=1,penirq=17,penirq_pull=2,speed=1000000,keep_vref_on=1,swapxy=1,pmax=255,xohms=60,xmin=200,xmax=3900,ymin=200,ymax=3900\n',
			'DISPLAY_WIDTH': '480',
			'DISPLAY_HEIGHT': '320',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['WaveShare 3.5B', {
			'DISPLAY_CONFIG': 
				'dtoverlay=waveshare35b\n'+
				'#dtoverlay=ads7846,cs=1,penirq=17,penirq_pull=2,speed=1000000,keep_vref_on=1,swapxy=1,pmax=255,xohms=60,xmin=200,xmax=3900,ymin=200,ymax=3900\n',
			'DISPLAY_WIDTH': '480',
			'DISPLAY_HEIGHT': '320',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['WaveShare 3.5B V2', {
			'DISPLAY_CONFIG': 
				'dtoverlay=waveshare35b-v2\n'+
				'#dtoverlay=ads7846,cs=1,penirq=17,penirq_pull=2,speed=1000000,keep_vref_on=1,swapxy=1,pmax=255,xohms=60,xmin=200,xmax=3900,ymin=200,ymax=3900\n',
			'DISPLAY_WIDTH': '480',
			'DISPLAY_HEIGHT': '320',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['WaveShare 3.5C', {
			'DISPLAY_CONFIG':
				'dtoverlay=waveshare35c:rotate=90\n'+
				'#dtoverlay=ads7846,cs=1,penirq=17,penirq_pull=2,speed=1000000,keep_vref_on=1,swapxy=1,pmax=255,xohms=60,xmin=200,xmax=3900,ymin=200,ymax=3900\n',
			'DISPLAY_WIDTH': '480',
			'DISPLAY_HEIGHT': '320',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['WaveShare 4A GPIO-only', {
			'DISPLAY_CONFIG': 
				'dtoverlay=waveshare35a:rotate=90\n'+
				'#dtoverlay=ads7846,cs=1,penirq=17,penirq_pull=2,speed=1000000,keep_vref_on=1,swapxy=1,pmax=255,xohms=60,xmin=200,xmax=3900,ymin=200,ymax=3900\n',
			'DISPLAY_WIDTH': '480',
			'DISPLAY_HEIGHT': '320',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['WaveShare 4c GPIO-only', {
			'DISPLAY_CONFIG': 
				'dtoverlay=waveshare4c:rotate=90\n'+
				'#dtoverlay=ads7846,cs=1,penirq=17,penirq_pull=2,speed=1000000,keep_vref_on=1,swapxy=1,pmax=255,xohms=60,xmin=200,xmax=3900,ymin=200,ymax=3900\n',
			'DISPLAY_WIDTH': '480',
			'DISPLAY_HEIGHT': '320',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['WaveShare 4 HDMI+GPIO', {
			'DISPLAY_CONFIG':
				'display_rotate=3\n'+
				'hdmi_drive=1\n'+
				'hdmi_force_hotplug=1\n'+
				'hdmi_group=2\n'+
				'hdmi_mode=87\n'+
				'hdmi_timings=480 0 40 10 80 800 0 13 3 32 0 0 0 60 0 32000000 3\n'+
				'dtoverlay=ads7846,cs=1,penirq=25,penirq_pull=2,speed=50000,keep_vref_on=0,swapxy=0,pmax=255,xohms=150,xmin=983,xmax=63241,ymin=3015,ymax=62998\n',
			'DISPLAY_WIDTH': '800',
			'DISPLAY_HEIGHT': '480',
			'FRAMEBUFFER': '/dev/fb0'
		}],
		['WaveShare 4.3 HDMI+GPIO', {
			'DISPLAY_CONFIG': 
				'display_rotate=2\n'+
				'hdmi_force_hotplug=1\n'+
				'hdmi_group=2\n'+
				'hdmi_mode=87\n'+
				'hdmi_drive=1\n'+
				'hdmi_timings=480 0 1 41 2 272 0 2 10 2 0 0 0 60 0 9009000 3\n'+
				'dtoverlay=ads7846,cs=1,penirq=25,penirq_pull=2,speed=50000,keep_vref_on=0,swapxy=0,pmax=255,xohms=150,xmin=200,xmax=3900,ymin=200,ymax=3900',
			'DISPLAY_WIDTH': '800',
			'DISPLAY_HEIGHT': '480',
			'FRAMEBUFFER': '/dev/fb0'
		}],
		['WaveShare 5 HDMI+GPIO', {
			'DISPLAY_CONFIG':
				'hdmi_force_hotplug=1\n'+
				'hdmi_drive=1\n'+
				'hdmi_group=2\n'+
				'hdmi_mode=1\n'+
				'hdmi_mode=87\n'+
				'hdmi_cvt 800 480 60 6 0 0 0\n'+
				'dtoverlay=ads7846,cs=1,penirq=25,penirq_pull=2,speed=50000,keep_vref_on=0,swapxy=0,pmax=255,xohms=150,xmin=200,xmax=3900,ymin=200,ymax=3900',
			'DISPLAY_WIDTH': '800',
			'DISPLAY_HEIGHT': '480',
			'FRAMEBUFFER': '/dev/fb0'
		}],
		['WaveShare 5 HDMI+USB', {
			'DISPLAY_CONFIG': 
				'hdmi_force_hotplug=1\n'+
				'hdmi_drive=1\n'+
				'hdmi_group=2\n'+
				'hdmi_mode=1\n'+
				'hdmi_mode=87\n'+
				'hdmi_cvt 800 480 60 6 0 0 0',
			'DISPLAY_WIDTH': '800',
			'DISPLAY_HEIGHT': '480',
			'FRAMEBUFFER': '/dev/fb0'
		}],
		['WaveShare 7 HDMI+GPIO 1024x600', {
			'DISPLAY_CONFIG':
				'hdmi_force_hotplug=1\n'+
				'hdmi_drive=2\n'+
				'hdmi_group=2\n'+
				'hdmi_mode=1\n'+
				'hdmi_mode=87\n'+
				'hdmi_cvt 1024 600 60 6 0 0 0\n'+
				'dtoverlay=ads7846,cs=1,penirq=25,penirq_pull=2,speed=50000,keep_vref_on=0,swapxy=0,pmax=255,xohms=150,xmin=200,xmax=3900,ymin=200,ymax=3900',
			'DISPLAY_WIDTH': '1024',
			'DISPLAY_HEIGHT': '600',
			'FRAMEBUFFER': '/dev/fb0'
		}],
		['WaveShare 7 HDMI+GPIO 800x480', {
			'DISPLAY_CONFIG':
				'hdmi_force_hotplug=1\n'+
				'hdmi_drive=2\n'+
				'hdmi_group=2\n'+
				'hdmi_mode=1\n'+
				'hdmi_mode=87\n'+
				'hdmi_cvt 800 480 60 6 0 0 0\n'+
				'dtoverlay=ads7846,cs=1,penirq=25,penirq_pull=2,speed=50000,keep_vref_on=0,swapxy=0,pmax=255,xohms=150,xmin=200,xmax=3900,ymin=200,ymax=3900',
			'DISPLAY_WIDTH': '800',
			'DISPLAY_HEIGHT': '480',
			'FRAMEBUFFER': '/dev/fb0'
		}],
		['WaveShare 7 HDMI+USB 1024x600', {
			'DISPLAY_CONFIG':
				'hdmi_force_hotplug=1\n'+
				'hdmi_drive=1\n'+
				'hdmi_group=2\n'+
				'hdmi_mode=1\n'+
				'hdmi_mode=87\n'+
				'hdmi_cvt 1024 600 60 6 0 0 0',
			'DISPLAY_WIDTH': '1024',
			'DISPLAY_HEIGHT': '600',
			'FRAMEBUFFER': '/dev/fb0'
		}],
		['WaveShare 7 HDMI+USB 800x480', {
			'DISPLAY_CONFIG':
				'hdmi_force_hotplug=1\n'+
				'hdmi_drive=1\n'+
				'hdmi_group=2\n'+
				'hdmi_mode=1\n'+
				'hdmi_mode=87\n'+
				'hdmi_cvt 800 480 60 6 0 0 0',
			'DISPLAY_WIDTH': '800',
			'DISPLAY_HEIGHT': '480',
			'FRAMEBUFFER': '/dev/fb0'
		}],
		['Sainsmart 1.8', {
			'DISPLAY_CONFIG': 'dtoverlay=sainsmart18,rotate=90',
			'DISPLAY_WIDTH': '160',
			'DISPLAY_HEIGHT': '128',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['MHS35 480x320', {
			'DISPLAY_CONFIG': 'dtoverlay=mhs35,rotate=90',
			'DISPLAY_WIDTH': '480',
			'DISPLAY_HEIGHT': '320',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['MPI5008 800x480', {
			'DISPLAY_CONFIG': 
				'hdmi_force_hotplug=1\n'+
				'dtparam=i2c_arm=on\n'+
				'dtparam=spi=on\n'+
				'enable_uart=1\n'+
				'display_rotate=0\n'+
				'max_usb_current=1\n'+
				'config_hdmi_boost=7\n'+
				'hdmi_group=2\n'+
				'hdmi_mode=1\n'+
				'hdmi_mode=87\n'+
				'hdmi_drive=1\n'+
				'hdmi_cvt 800 480 60 6 0 0 0\n'+
				'dtoverlay=ads7846,cs=1,penirq=25,penirq_pull=2,speed=50000,keep_vref_on=0,swapxy=0,pmax=255,xohms=150,xmin=200,xmax=3900,ymin=200,ymax=3900',
			'DISPLAY_WIDTH': '800',
			'DISPLAY_HEIGHT': '480',
			'FRAMEBUFFER': '/dev/fb0'
		}],
		['Pi 7 Touchscreen Display 800x480', {
			'DISPLAY_CONFIG':
				'lcd_rotate=2\n'+
				'dtoverlay=rpi-ft5406\n',
			'DISPLAY_WIDTH': '800',
			'DISPLAY_HEIGHT': '480',
			'FRAMEBUFFER': '/dev/fb0'
		}],
		['MIPI DSI 800x480', {
			'DISPLAY_CONFIG': '',
			'DISPLAY_WIDTH': '800',
			'DISPLAY_HEIGHT': '480',
			'FRAMEBUFFER': '/dev/fb0'
		}]
		['Generic HDMI Display', {
			'DISPLAY_CONFIG': 'disable_overscan=1\n',
			'DISPLAY_WIDTH': '',
			'DISPLAY_HEIGHT': '',
			'FRAMEBUFFER': '/dev/fb0'
		}],
		['Generic 4k HDMI Display', {
			'DISPLAY_CONFIG':
				'disable_overscan=1\n'+
				'hdmi_enable_4kp60=1\n',
			'DISPLAY_WIDTH': '',
			'DISPLAY_HEIGHT': '',
			'FRAMEBUFFER': '/dev/fb0'
		}],
		['Custom Device', {
			'DISPLAY_CONFIG': '',
			'DISPLAY_WIDTH': '',
			'DISPLAY_HEIGHT': '',
			'FRAMEBUFFER': ''
		}]
	])

	@tornado.web.authenticated
	def get(self, errors=None):

		config=OrderedDict()

		if os.environ.get('ZYNTHIAN_KIT_VERSION')!='Custom':
			custom_options_disabled = True
			config['ZYNTHIAN_MESSAGE'] = {
				'type': 'html',
				'content': "<div class='alert alert-warning'>Some config options are disabled. You may want to <a href='/hw-kit'>choose Custom Kit</a> for enabling all options.</div>"
			}
		else:
			custom_options_disabled = False

		display_names = list(self.display_presets.keys())
		config['DISPLAY_NAME'] = {
			'type': 'select',
			'title': "Display",
			'value': os.environ.get('DISPLAY_NAME'),
			'options': display_names,
			'option_labels': OrderedDict([(opt, opt) for opt in display_names]),
			'presets': self.display_presets,
			'disabled': custom_options_disabled
		}
		config['DISPLAY_CONFIG'] = {
			'type': 'textarea',
			'rows': 4,
			'cols': 50,
			'title': 'Config',
			'value': os.environ.get('DISPLAY_CONFIG'),
			'advanced': True,
			'disabled': custom_options_disabled
		}
		config['DISPLAY_WIDTH'] = {
			'type': 'text',
			'title': 'Width',
			'value': os.environ.get('DISPLAY_WIDTH'),
			'advanced': True,
			'disabled': custom_options_disabled
		}
		config['DISPLAY_HEIGHT'] = {
			'type': 'text',
			'title': 'Height',
			'value': os.environ.get('DISPLAY_HEIGHT'),
			'advanced': True,
			'disabled': custom_options_disabled
		}
		config['FRAMEBUFFER'] = {
			'type': 'text',
			'title': 'Framebuffer',
			'value': os.environ.get('FRAMEBUFFER'),
			'advanced': True,
			'disabled': custom_options_disabled
		}

		super().get("Display", config, errors)


	@tornado.web.authenticated
	def post(self):
		errors=self.update_config(tornado.escape.recursive_unicode(self.request.arguments))
		self.delete_fb_splash() # New splash-screens will be generated on next boot

		self.reboot_flag = True
		self.get(errors)


	@classmethod
	def delete_fb_splash(cls):
		try:
			cmd="rm -rf %s/img" % os.environ.get('ZYNTHIAN_CONFIG_DIR')
			check_output(cmd, shell=True)
		except Exception as e:
			logging.error("Deleting FrameBuffer Splash Screens: %s" % e)

