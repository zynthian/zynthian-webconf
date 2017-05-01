#!/usr/bin/python3
# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
# 
# Web Service API
# 
# Copyright (C) 2015-2017 Fernando Moyano <jofemodo@zynthian.org>
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
import sys
import logging
import tornado.ioloop
import tornado.web
from subprocess import check_output
from collections import OrderedDict

#------------------------------------------------------------------------------

#Configure Logging
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

#------------------------------------------------------------------------------
# Zynthian Config Handler
#------------------------------------------------------------------------------

class ZynthianConfigHandler(tornado.web.RequestHandler):

	def prepare(self):
		self.genjson=False
		try:
			if self.get_query_argument("json"):
				self.genjson=True
		except:
			pass

	def update_config(self, config):
		# Get config file content
		fpath=os.environ.get('ZYNTHIAN_SYS_DIR')+"/scripts/zynthian_envars.sh"
		if not os.path.isfile(fpath):
			fpath="./zynthian_envars.sh"
		with open(fpath) as f:
			lines = f.readlines()

		# Find and replace lines to update
		pattern=re.compile("^export ([^\s]*)=")
		for i,line in enumerate(lines):
			res=pattern.match(line)
			if res:
				varname=res.group(1)
				if varname in config:
					os.environ[varname]=config[varname][0]
					lines[i]="export %s=\"%s\"\n" % (varname,config[varname][0])
					logging.info(lines[i],end='')

		# Write updated config file
		with open(fpath,'w') as f:
			f.writelines(lines)

		# Update System Configuration
		try:
			check_output(os.environ.get('ZYNTHIAN_SYS_DIR')+"/scripts/update_zynthian_sys.sh", shell=True)
		except Exception as e:
			logging.error("Updating Sytem Config: %s" % e)


#------------------------------------------------------------------------------
# Audio Configuration
#------------------------------------------------------------------------------

class AudioConfigHandler(ZynthianConfigHandler):

	soundcard_presets=OrderedDict([
		['HifiBerry DAC+', { 
			'SOUNDCARD_DTOVERLAY': 'hifiberry-dacplus'
		}],
		['HifiBerry DAC', { 
			'SOUNDCARD_DTOVERLAY':'hifiberry-dac'
		}],
		['HifiBerry Digi', { 
			'SOUNDCARD_DTOVERLAY':'hifiberry-digi'
		}],
		['HifiBerry Amp', { 
			'SOUNDCARD_DTOVERLAY': 'hifiberry-amp'
		}],
		['AudioInjector', { 
			'SOUNDCARD_DTOVERLAY': 'audioinjector-wm8731-audio'
		}],
		['IQAudio DAC', { 
			'SOUNDCARD_DTOVERLAY': 'iqaudio-dac'
		}],
		['IQAudio DAC+', { 
			'SOUNDCARD_DTOVERLAY': 'iqaudio-dacplus'
		}],
		['IQAudio Digi', { 
			'SOUNDCARD_DTOVERLAY': 'iqaudio-digi-wm8804-audio'
		}],
		['PiSound', { 
			'SOUNDCARD_DTOVERLAY': 'pisound'
		}],
		['JustBoom DAC', { 
			'SOUNDCARD_DTOVERLAY': 'justboom-dac'
		}],
		['JustBoom Digi', { 
			'SOUNDCARD_DTOVERLAY': 'justboom-digi'
		}],
		['USB device', { 
			'SOUNDCARD_DTOVERLAY': ''
		}]
	])

	def get(self):
		config=OrderedDict([
			['SOUNDCARD_NAME', {
				'type': 'select',
				'title': 'Soundcard',
				'value': os.environ.get('SOUNDCARD_NAME'),
				'options': list(self.soundcard_presets.keys()),
				'presets': self.soundcard_presets
			}],
			['SOUNDCARD_DTOVERLAY', {
				'type': 'text',
				'title': 'Overlay',
				'value': os.environ.get('SOUNDCARD_DTOVERLAY'),
				'advanced': True
			}],
			['JACKD_OPTIONS', {
				'type': 'text',
				'title': 'Jackd Options',
				'value': os.environ.get('JACKD_OPTIONS'),
				'advanced': True
			}]
		])
		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", config=config, title="Audio")

	def post(self):
		self.update_config(tornado.escape.recursive_unicode(self.request.arguments))
		self.get()

#------------------------------------------------------------------------------
# Display Configuration
#------------------------------------------------------------------------------

class DisplayConfigHandler(ZynthianConfigHandler):

	display_presets=OrderedDict([
		['PiTFT 2.8 Resistive', {
			'DISPLAY_DTOVERLAY': 'pitft28-resistive,rotate=90,speed=32000000,fps=20',
			'DISPLAY_WIDTH': '320',
			'DISPLAY_HEIGHT': '240',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['PiTFT 2.8 Capacitive', {
			'DISPLAY_DTOVERLAY': 'pitft28-capacitive,rotate=90,speed=32000000,fps=20',
			'DISPLAY_WIDTH': '320',
			'DISPLAY_HEIGHT': '240',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['PiTFT 3.5 Resistive', {
			'DISPLAY_DTOVERLAY': 'pitft35-resistive,rotate=90,speed=32000000,fps=20',
			'DISPLAY_WIDTH': '480',
			'DISPLAY_HEIGHT': '320',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['PiScreen 3.5 (v1)', {
			'DISPLAY_DTOVERLAY': 'piscreen,speed=16000000,rotate=90',
			'DISPLAY_WIDTH': '480',
			'DISPLAY_HEIGHT': '320',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['PiScreen 3.5 (v2)', {
			'DISPLAY_DTOVERLAY': 'piscreen2r',
			'DISPLAY_WIDTH': '480',
			'DISPLAY_HEIGHT': '320',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['RPi-Display 2.8', {
			'DISPLAY_DTOVERLAY': 'rpi-display,speed=32000000,rotate=270',
			'DISPLAY_WIDTH': '320',
			'DISPLAY_HEIGHT': '240',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['HDMI display', {
			'DISPLAY_DTOVERLAY': '',
			'DISPLAY_WIDTH': '',
			'DISPLAY_HEIGHT': '',
			'FRAMEBUFFER': '/dev/fb0'
		}]
	])
	
	def get(self):
		config=OrderedDict([
			['DISPLAY_NAME', {
				'type': 'select',
				'title': 'Display',
				'value': os.environ.get('DISPLAY_NAME'),
				'options': list(self.display_presets.keys()),
				'presets': self.display_presets
			}],
			['DISPLAY_DTOVERLAY', {
				'type': 'text',
				'title': 'Overlay',
				'value': os.environ.get('DISPLAY_DTOVERLAY'),
				'advanced': True
			}],
			['DISPLAY_WIDTH', {
				'type': 'text',
				'title': 'Width',
				'value': os.environ.get('DISPLAY_WIDTH'),
				'advanced': True
			}],
			['DISPLAY_HEIGHT', {
				'type': 'text',
				'title': 'Height',
				'value': os.environ.get('DISPLAY_HEIGHT'),
				'advanced': True
			}],
			['FRAMEBUFFER', {
				'type': 'text',
				'title': 'Frambuffer',
				'value': os.environ.get('FRAMEBUFFER'),
				'advanced': True
			}]
		])
		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", config=config, title="Display")

	def post(self):
		self.update_config(tornado.escape.recursive_unicode(self.request.arguments))
		self.get()

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
		["PROTOTYPE-KEES", {
			'ZYNTHIAN_WIRING_ENCODER_A': "27,21,4,5",
			'ZYNTHIAN_WIRING_ENCODER_B': "25,26,31,7",
			'ZYNTHIAN_WIRING_SWITCHES': "23,107,6,106"
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

	def get(self):
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
			self.render("config.html", config=config, title="Wiring")

	def post(self):
		self.update_config(tornado.escape.recursive_unicode(self.request.arguments))
		self.get()

#------------------------------------------------------------------------------
# UI Configuration
#------------------------------------------------------------------------------

class UIConfigHandler(ZynthianConfigHandler):

	font_families=[
		"Audiowide",
		"Helvetica",
		"Economica",
		"Orbitron",
		"Abel"
	]

	def get(self):
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
			self.render("config.html", config=config, title="User Interface")

	def post(self):
		self.update_config(tornado.escape.recursive_unicode(self.request.arguments))
		self.get()


#------------------------------------------------------------------------------
# Build Web App & Start Server
#------------------------------------------------------------------------------

def make_app():
	return tornado.web.Application([
		(r'/$', AudioConfigHandler),
		#(r'/()$', tornado.web.StaticFileHandler, {'path': 'html', "default_filename": "index.html"}),
		(r'/(.*\.html)$', tornado.web.StaticFileHandler, {'path': 'html'}),
		(r'/(favicon\.ico)$', tornado.web.StaticFileHandler, {'path': 'img'}),
		(r'/img/(.*)$', tornado.web.StaticFileHandler, {'path': 'img'}),
		(r'/css/(.*)$', tornado.web.StaticFileHandler, {'path': 'css'}),
		(r'/js/(.*)$', tornado.web.StaticFileHandler, {'path': 'js'}),
		(r'/bower_components/(.*)$', tornado.web.StaticFileHandler, {'path': 'bower_components'}),
		(r"/api/audio$", AudioConfigHandler),
		(r"/api/display$", DisplayConfigHandler),
		(r"/api/wiring$", WiringConfigHandler),
		(r"/api/ui$", UIConfigHandler),
	], template_path="templates")

if __name__ == "__main__":
	app = make_app()
	app.listen(80)
	tornado.ioloop.IOLoop.current().start()

#------------------------------------------------------------------------------
