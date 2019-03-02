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


import logging


import tornado.web
import jsonpickle
from collections import OrderedDict
import mido

import asyncio

from lib.tail_thread import TailThread
from lib.zynthian_websocket_handler import ZynthianWebSocketMessageHandler, ZynthianWebSocketMessage


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
        config=OrderedDict([])
        if self.genjson:
            self.write(config)
        else:
            self.render("config.html", body="midi_log.html", config=config, title="MIDI Log", errors=errors)

    @tornado.web.authenticated
    def post(self):
        self.get()


class MidiTailThread(TailThread):

    def run(self):
        mido.set_backend('mido.backends.rtmidi/UNIX_JACK')
        with mido.open_input("ZynMidiRouter:main_out") as inport:
            for msg in inport:
                message = ZynthianWebSocketMessage('MidiLogMessageHandler', msg)
                self.websocket.write_message(jsonpickle.encode(message))


class MidiLogMessageHandler(ZynthianWebSocketMessageHandler):
    logging_thread = None

    @classmethod
    def is_registered_for(cls, handler_name):
        return handler_name == 'MidiLogMessageHandler'

    def spawn_tail_thread(self):
        logging.info("spawn_tail_thread")
        loop = asyncio.get_event_loop()
        MidiLogMessageHandler.logging_thread = MidiTailThread(self.websocket, loop)
        MidiLogMessageHandler.logging_thread.start()

    def do_start_logging(self):
        logging.info("start midi logging")
        if MidiLogMessageHandler.logging_thread:
            MidiLogMessageHandler.logging_thread.stop()

        self.spawn_tail_thread()

    def on_websocket_message(self, action):
        logging.debug("action: %s " % action)
        if action == 'SHOW_LOGGING':
            self.do_start_logging()

        logging.debug("message handled.")  # this needs to show up early to get the socket working again.

    def on_close(self):
        logging.info("stopping tail threads")
        if MidiLogMessageHandler.logging_thread:
            MidiLogMessageHandler.logging_thread.stop()
