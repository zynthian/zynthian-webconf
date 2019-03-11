# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# UI Configuration Handler
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
import jsonpickle
import mido
import asyncio
from collections import OrderedDict
from lib.tail_thread import TailThread
from lib.zynthian_websocket_handler import ZynthianWebSocketMessageHandler, ZynthianWebSocketMessage
from lib.midi_config_handler import get_ports_config

#------------------------------------------------------------------------------
# UI Configuration
#------------------------------------------------------------------------------

class MidiLogHandler(tornado.web.RequestHandler):

	def get_current_user(self):
		return self.get_secure_cookie("user")


	def prepare(self):
		self.genjson = False
		try:
			if self.get_query_argument("json"):
				self.genjson = True
		except:
			pass


	@tornado.web.authenticated
	def get(self, errors=None):
		try:
			self.midi_port = self.request.arguments['MIDI_PORT']
		except:
			self.midi_port = "ZynMidiRouter:main_out"

		config=OrderedDict([
			['MIDI_PORT',  self.midi_port],
			['MIDI_PORTS', self.get_midi_in_ports()]
		])

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="midi_log.html", config=config, title="MIDI Log", errors=errors)


	@tornado.web.authenticated
	def post(self):
		self.get()


	@staticmethod
	def get_midi_in_ports():
		#Get current MIDI ports configuration
		try:
			current_midi_ports = os.environ.get('ZYNTHIAN_MIDI_PORTS').replace("\\n","\n")
		except:
			current_midi_ports = ""		
		ports_config=get_ports_config(current_midi_ports)
		# Input Input Devices:
		midi_in_ports = ports_config['IN']
		# Add Zynthian Router output ports:
		midi_in_ports.append({
			'name': "ZynMidiRouter:main_out",
			'shortname': "main_out",
			'alias': "ZynMidiRouter Main",
		})
		midi_in_ports.append({
			'name': "ZynMidiRouter:net_out",
			'shortname': "net_out",
			'alias': "ZynMidiRouter Network" 
		})
		midi_in_ports.append({
			'name': "ZynMidiRouter:ctrl_out",
			'shortname': "ctrl_out",
			'alias': "ZynMidiRouter Feedback" 
		})
		for i in range(0,16):
			midi_in_ports.append({
				'name': "ZynMidiRouter:ch{}_out".format(i),
				'shortname': "ch{}_out".format(i),
				'alias': "ZynMidiRouter CH#{}".format(i) 
			})
		return midi_in_ports


class MidiLogMessageHandler(ZynthianWebSocketMessageHandler):
	mido_port = None
	midi_port_name = None

	@classmethod
	def is_registered_for(cls, handler_name):
		return handler_name == 'MidiLogMessageHandler'


	def do_start_logging(self, midi_port_name):
		logging.info("start midi logging on {}".format(midi_port_name))

		self.do_stop_logging()
		MidiLogMessageHandler.midi_port_name = midi_port_name

		try:
			mido.set_backend('mido.backends.rtmidi/UNIX_JACK')
			MidiLogMessageHandler.mido_port = mido.open_input(self.midi_port_name, callback=self.on_midi_in)
		except:
			logging.error("Can't open MIDI Port {}".format(self.midi_port_name))


	def on_midi_in(self, msg):
		message = ZynthianWebSocketMessage('MidiLogMessageHandler', msg)
		self.websocket.write_message(jsonpickle.encode(message))


	def do_stop_logging(self):
		if MidiLogMessageHandler.mido_port:
			logging.info("stop midi logging")
			MidiLogMessageHandler.mido_port.close()
			MidiLogMessageHandler.mido_port.callback = None
		else:
			logging.info("No MIDO to Stop!!??")


	def on_websocket_message(self, message):
		logging.debug("message: %s " % message)
		parts = message.split(" ", maxsplit=1)
		action = parts[0]

		if action == 'START_LOGGING':
			try:
				midi_port_name = parts[1]
			except:
				midi_port_name = "ZyntMidiRouter:main_out"
			self.do_start_logging(midi_port_name)

		elif action == 'STOP_LOGGING':
			self.do_stop_logging()

		elif action == 'GET_MIDI_PORT':
			self.websocket.write_message("MIDI_PORT = {}".format(self.midi_port_name))

		logging.debug("message handled.")  # this needs to show up early to get the socket working again.


	def on_close(self):
		logging.info("stopping tail threads")
		self.do_stop_logging()
