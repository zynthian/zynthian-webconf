# -*- coding: utf-8 -*-
# ********************************************************************
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
# ********************************************************************

import mido
import logging
import jsonpickle
import tornado.web
from lib.zynthian_config_handler import ZynthianBasicHandler
from lib.zynthian_websocket_handler import ZynthianWebSocketMessageHandler, ZynthianWebSocketMessage
from lib.midi_config_handler import get_ports_config

# ------------------------------------------------------------------------------
# UI Configuration
# ------------------------------------------------------------------------------


class MidiLogHandler(ZynthianBasicHandler):

	@tornado.web.authenticated
	def get(self, errors=None):
		try:
			self.midi_port = self.request.arguments['MIDI_PORT']
		except:
			self.midi_port = "ZynMidiRouter:step_out"

		config = {
			'MIDI_PORT': self.midi_port,
			'MIDI_PORTS': self.get_midi_in_ports()
		}

		super().get("midi_log.html", "MIDI Log", config, errors)

	@tornado.web.authenticated
	def post(self):
		self.get()

	@staticmethod
	def get_midi_in_ports():
		# Get MIDI ports
		ports_config = get_ports_config()
		# MIDI Input Devices
		midi_in_ports = ports_config['IN']
		# Add Zynthian Router output ports:
		midi_in_ports.append({
			'name': "ZynMidiRouter:mod_out",
			'shortname': "mod_out",
			'alias': "ZynMidiRouter => MOD-UI",
		})
		midi_in_ports.append({
			'name': "ZynMidiRouter:step_out",
			'shortname': "step_out",
			'alias': "ZynMidiRouter => Step Sequencer"
		})
		midi_in_ports.append({
			'name': "ZynMidiRouter:ctrl_out",
			'shortname': "ctrl_out",
			'alias': "ZynMidiRouter => Control Feedback"
		})
		for i in range(0, 16):
			midi_in_ports.append({
				'name': "ZynMidiRouter:ch{}_out".format(i),
				'shortname': "ch{}_out".format(i),
				'alias': "ZynMidiRouter => CH#{}".format(i+1)
			})
		for i in range(0, 24):
			midi_in_ports.append({
				'name': "ZynMidiRouter:dev{}_out".format(i),
				'shortname': "dev{}_out".format(i),
				'alias': "ZynMidiRouter => DEV#{}".format(i+1)
			})
		midi_in_ports.append({
			'name': "ZynMaster:midi_out",
			'shortname': "midi_out",
			'alias': "MIDI => CV/Gate",
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
		except Exception as err:
			logging.error("Can't open MIDI Port {}: {}".format(self.midi_port_name, err))

	def on_midi_in(self, msg):
		message = ZynthianWebSocketMessage('MidiLogMessageHandler', msg)
		self.websocket.write_message(jsonpickle.encode(message))

	def do_stop_logging(self):
		if MidiLogMessageHandler.mido_port:
			logging.info("stop midi logging")
			MidiLogMessageHandler.mido_port.close()

	def on_websocket_message(self, message):
		logging.debug("message: %s " % message)
		parts = message.split(" ", maxsplit=1)
		action = parts[0]

		if action == 'START_LOGGING':
			try:
				midi_port_name = parts[1]
			except:
				midi_port_name = "ZyntMidiRouter:step_out"
			self.do_start_logging(midi_port_name)

		elif action == 'STOP_LOGGING':
			self.do_stop_logging()

		elif action == 'GET_MIDI_PORT':
			self.websocket.write_message("MIDI_PORT = {}".format(self.midi_port_name))

		logging.debug("message handled.")  # this needs to show up early to get the socket working again.

	def on_close(self):
		logging.info("stopping tail threads")
		self.do_stop_logging()
