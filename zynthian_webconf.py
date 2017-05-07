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
		pattern=re.compile("^export ([^\s]*?)=")
		for i,line in enumerate(lines):
			res=pattern.match(line)
			if res:
				varname=res.group(1)
				if varname in config:
					value=config[varname][0].replace("\n", "\\n")
					value=value.replace("\r", "")
					os.environ[varname]=value
					lines[i]="export %s=\"%s\"\n" % (varname,value)
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
		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="config_block.html", config=config, title="Audio", errors=errors)

	def post(self):
		errors=self.update_config(tornado.escape.recursive_unicode(self.request.arguments))
		self.get(errors)

#------------------------------------------------------------------------------
# Display Configuration
#------------------------------------------------------------------------------

class DisplayConfigHandler(ZynthianConfigHandler):

	display_presets=OrderedDict([
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
		['PiScreen 3.5 (v1)', {
			'DISPLAY_CONFIG': 'dtoverlay=piscreen,speed=16000000,rotate=90',
			'DISPLAY_WIDTH': '480',
			'DISPLAY_HEIGHT': '320',
			'FRAMEBUFFER': '/dev/fb1'
		}],
		['PiScreen 3.5 (v2)', {
			'DISPLAY_CONFIG': 'dtoverlay=piscreen2r',
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
		['WaveShare 5 HDMI/GPIO', {
			'DISPLAY_CONFIG': 'hdmi_drive=1\n'+
				'hdmi_group=2\n'+
				'hdmi_mode=1\n'+
				'hdmi_mode=87\n'+
				'hdmi_cvt 800 480 60 6 0 0 0\n'+
				'dtoverlay=ads7846,cs=1,penirq=25,penirq_pull=2,speed=20000,keep_vref_on=0,swapxy=0,pmax=255,xohms=150,xmin=200,xmax=3900,ymin=200,ymax=3900',
			'DISPLAY_WIDTH': '800',
			'DISPLAY_HEIGHT': '480',
			'FRAMEBUFFER': '/dev/fb0'
		}],
		['WaveShare 5 HDMI/USB', {
			'DISPLAY_CONFIG': 'hdmi_drive=1\n'+
				'hdmi_group=2\n'+
				'hdmi_mode=1\n'+
				'hdmi_mode=87\n'+
				'hdmi_cvt 800 480 60 6 0 0 0',
			'DISPLAY_WIDTH': '800',
			'DISPLAY_HEIGHT': '480',
			'FRAMEBUFFER': '/dev/fb0'
		}],
		['WaveShare 7 HDMI/GPIO', {
			'DISPLAY_CONFIG': 'hdmi_drive=1\n'+
				'hdmi_group=2\n'+
				'hdmi_mode=1\n'+
				'hdmi_mode=87\n'+
				'hdmi_cvt 1024 600 60 6 0 0 0\n'+
				'dtoverlay=ads7846,cs=1,penirq=25,penirq_pull=2,speed=20000,keep_vref_on=0,swapxy=0,pmax=255,xohms=150,xmin=200,xmax=3900,ymin=200,ymax=3900',
			'DISPLAY_WIDTH': '1024',
			'DISPLAY_HEIGHT': '600',
			'FRAMEBUFFER': '/dev/fb0'
		}],
		['WaveShare 7 HDMI/USB', {
			'DISPLAY_CONFIG': 'hdmi_drive=1\n'+
				'hdmi_group=2\n'+
				'hdmi_mode=1\n'+
				'hdmi_mode=87\n'+
				'hdmi_cvt 1024 600 60 6 0 0 0',
			'DISPLAY_WIDTH': '1024',
			'DISPLAY_HEIGHT': '600',
			'FRAMEBUFFER': '/dev/fb0'
		}],
		['HDMI Generic display', {
			'DISPLAY_CONFIG': '',
			'DISPLAY_WIDTH': '',
			'DISPLAY_HEIGHT': '',
			'FRAMEBUFFER': '/dev/fb0'
		}]
	])
	
	def get(self, errors=None):
		config=OrderedDict([
			['DISPLAY_NAME', {
				'type': 'select',
				'title': 'Display',
				'value': os.environ.get('DISPLAY_NAME'),
				'options': list(self.display_presets.keys()),
				'presets': self.display_presets
			}],
			['DISPLAY_CONFIG', {
				'type': 'textarea',
				'title': 'Config',
				'value': os.environ.get('DISPLAY_CONFIG'),
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
			self.render("config.html", body="config_block.html", config=config, title="Display", errors=errors)

	def post(self):
		errors=self.update_config(tornado.escape.recursive_unicode(self.request.arguments))
		self.get(errors)

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


#------------------------------------------------------------------------------
# System Menu
#------------------------------------------------------------------------------

class SystemConfigHandler(ZynthianConfigHandler):

	def get(self, errors=None):
		#Get Hostname
		with open("/etc/hostname") as f:
			hostname=f.readline()

		config=OrderedDict([
			['HOSTNAME', {
				'type': 'text',
				'title': 'Hostname',
				'value': hostname
			}],
			['PASSWORD', {
				'type': 'password',
				'title': 'Password',
				'value': '*'
			}],
			['REPEAT_PASSWORD', {
				'type': 'password',
				'title': 'Repeat password',
				'value': '*'
			}]
		])
		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="config_block.html", config=config, title="System", errors=errors)

	def post(self):
		errors=self.update_system_config(tornado.escape.recursive_unicode(self.request.arguments))
		self.get(errors)

	def update_system_config(self, config):
		#Update Hostname
		with open("/etc/hostname",'w') as f:
			f.write(config['HOSTNAME'][0])
		#Update Password
		if len(config['PASSWORD'][0])<6:
			return { 'PASSWORD': "Password must have at least 6 characters" }
		if config['PASSWORD'][0]!=config['REPEAT_PASSWORD'][0]:
			return { 'REPEAT_PASSWORD': "Passwords does not match!" }
		check_output("echo root:%s | chpasswd" % config['PASSWORD'][0], shell=True)

#------------------------------------------------------------------------------
# Reboot Hadler
#------------------------------------------------------------------------------

class RebootHandler(ZynthianConfigHandler):
	def get(self):
		if self.genjson:
			self.write("REBOOT")
		else:
			self.render("config.html", body="reboot_block.html", config=None, title="Reboot", errors=None)
		check_output("reboot", shell=True)

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
		(r"/api/system$", SystemConfigHandler),
		(r"/api/reboot$", RebootHandler),
	], template_path="templates")

if __name__ == "__main__":
	app = make_app()
	app.listen(80)
	tornado.ioloop.IOLoop.current().start()

#------------------------------------------------------------------------------
