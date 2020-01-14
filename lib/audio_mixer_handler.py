# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Audio Mixer Handler
#
# Copyright (C) 2019 Fernando Moyano <jofemodo@zynthian.org>
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
import jsonpickle
from typing import Optional, Awaitable

import tornado.web
from lib.audio_config_handler import AudioConfigHandler
from lib.zynthian_websocket_handler import ZynthianWebSocketMessageHandler, ZynthianWebSocketMessage
from zyngine.zynthian_engine_mixer import *


#------------------------------------------------------------------------------
# Audio Configuration
#------------------------------------------------------------------------------
class AudioMixerHandler(tornado.web.RequestHandler):

	websocket_message_handler_list = []

	def get_current_user(self):
		return self.get_secure_cookie("user")

	@tornado.web.authenticated
	def post(self, ctrl, val):
		result = {}

		try:
			logging.debug('updating webconfig view: {} with {}'.format(ctrl, val))

			for websocket_message_handler in AudioMixerHandler.websocket_message_handler_list:
				logging.debug('message_handler: {}'.format(websocket_message_handler))
				websocket_message_handler.update_controller_value(ctrl, val)


		except Exception as err:
			result['errors'] = str(err)
			logging.error(err)

		# JSON Ouput
		if result:
			self.write(result)

	@classmethod
	def register_websocket(self, websocket_message_handler:ZynthianWebSocketMessageHandler):
		AudioMixerHandler.websocket_message_handler_list.append(websocket_message_handler)

	@classmethod
	def unregister_websocket(self, websocket_message_handler: ZynthianWebSocketMessageHandler):
		AudioMixerHandler.websocket_message_handler_list.remove(websocket_message_handler)


class AudioConfigMessageHandler(ZynthianWebSocketMessageHandler):
	logging_thread = None

	@classmethod
	def is_registered_for(cls, handler_name):
		return handler_name == 'AudioConfigMessageHandler'


	def on_websocket_message(self, action_with_parameters):
		logging.debug("action: %s " % action_with_parameters)

		(action, parm1, parm2) = action_with_parameters.split("/")

		if action == 'UPDATE_AUDIO_MIXER':
			self.do_update_audio_mixer(parm1, parm2)
		elif action == 'REGISTER_WEBSOCKET':
			AudioMixerHandler.register_websocket(self)
		else:
			logging.error('Unknown action {}'.format(action))
		logging.debug("message handled.")  # this needs to show up early to get the socket working again.


	def on_close(self):
		AudioMixerHandler.unregister_websocket(self)


	def do_update_audio_mixer(self, symbol, value):
		try:
			zctrl = AudioConfigHandler.zctrls[symbol]
			if zctrl.is_toggle or zctrl.labels:
				zctrl.set_value(value)
			elif zctrl.is_integer:
				zctrl.set_value(int(value))

		except Exception as e:
			logging.debug("Can't set controller '{}' value to '{}': {}".format(symbol, value, e))


	def update_controller_value(self, symbol, value):
		message = ZynthianWebSocketMessage('AudioConfigMessageHandler', '{}={}'.format(symbol, value))
		self.websocket.write_message(jsonpickle.encode(message))

