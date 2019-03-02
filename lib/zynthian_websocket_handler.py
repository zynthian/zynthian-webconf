# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Zynthian Websocket Handler
#
# Copyright (C) 2017 Markus Heidt <markus@heidt-tech.com>
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


import logging
import tornado.websocket
import jsonpickle

#------------------------------------------------------------------------------
# Zynthian Websocket Handling
#------------------------------------------------------------------------------

def ZynthianWebSocketMessageHandlerFactory(handler_name, websocket):
	for cls in ZynthianWebSocketMessageHandler.__subclasses__():
		if cls.is_registered_for(handler_name):
			return cls(handler_name, websocket)
	raise ValueError


class ZynthianWebSocketMessageHandler(object):
	def __init__(self, handler_name, websocket):
		self.handler_name = handler_name
		self.websocket = websocket

	def on_open(self):
		pass

	def on_websocket_message(self, message):
		raise NotImplementedError("Please Implement on_websocket_message")

	def on_close(self):
		pass


class ZynthianWebSocketMessage(object):
	def __init__(self, handler_name, data):
		self._handler_name = handler_name
		self._data = data

	@property
	def handler_name(self):
		return self._handler_name

	@handler_name.setter
	def handler_name(self, value):
		self._handler_name = value

	@property
	def data(self):
		return self._data

	@data.setter
	def data(self, value):
		self._data = value


class ZynthianWebSocketHandler(tornado.websocket.WebSocketHandler):
	handlers = []

	def check_origin(self, origin):
		return True

	# the client connected
	def open(self):
		logging.info("New client connected to ZynthianWebSocketHandler")

	# the client sent the message
	def on_message(self, message):
		if message:
			decoded_message = jsonpickle.decode(message)
			logging.info("incoming ws message %s " % decoded_message)
			handler = ZynthianWebSocketMessageHandlerFactory(decoded_message['handler_name'], self)
			handler.on_websocket_message(decoded_message['data'])
			self.handlers.append(handler)

	# client disconnected
	def on_close(self):
		logging.info("Client disconnected")
		for handler in self.handlers:
			handler.on_close()
