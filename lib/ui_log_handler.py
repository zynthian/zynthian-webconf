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
import subprocess

import time

import tornado.web
from subprocess import check_output
import jsonpickle
from collections import OrderedDict


import asyncio

from lib.tail_thread import TailThread
from lib.zynthian_websocket_handler import ZynthianWebSocketMessageHandler, ZynthianWebSocketMessage


#------------------------------------------------------------------------------
# UI Configuration
#------------------------------------------------------------------------------
class UiLogHandler(tornado.web.RequestHandler):
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
            self.render("config.html", body="ui_log.html", config=config, title="UI Log", errors=errors)\

    @tornado.web.authenticated
    def post(self):
        self.get()


class UiLogMessageHandler(ZynthianWebSocketMessageHandler):
    logging_thread = None
    is_logging = True

    @classmethod
    def is_registered_for(cls, handler_name):
        return handler_name == 'UiLogMessageHandler'

    def get_process_command(self, debug_logging):
        service_name = ('zynthian_debug' if debug_logging else 'zynthian')
        logging.info("journalctl -f -u %s" % service_name)
        return "journalctl  -f -u %s" % service_name

    def spawn_tail_thread(self, debug_level):
        logging.info("spawn_tail_thread")
        loop = asyncio.get_event_loop()
        UiLogMessageHandler.logging_thread = TailThread(self.websocket, loop, self.get_process_command(debug_level))
        UiLogMessageHandler.logging_thread.start()

    def toggle_service(self, running_service, next_service):
        check_output("(systemctl stop %s)&" % running_service, shell=True)

        is_active = True
        while is_active:
            logging.info("getting status of %s" % running_service)
            try:
                check_output("systemctl status %s" % running_service, shell=True)
            except subprocess.CalledProcessError as e:
                for byte_line in e.output.splitlines():
                    line = byte_line.decode("utf-8")
                    logging.info(line)
                    if "Active:" in line and ("inactive" in line or "inactive" in line):
                        is_active = False

            time.sleep(1)

        check_output("(systemctl start %s)&" % next_service, shell=True)

    def do_start_debug_logging(self):
        logging.info("start debug logging")
        UiLogMessageHandler.logging_enabled = True
        message = ZynthianWebSocketMessage('UiLogMessageHandler', 'Restarting UI in debug mode')
        self.websocket.write_message(jsonpickle.encode(message))
        if UiLogMessageHandler.logging_thread:
            UiLogMessageHandler.logging_thread.stop()

        self.toggle_service("zynthian", "zynthian_debug")

        self.spawn_tail_thread(True)

    def do_stop_debug_logging(self):
        logging.info("stop debug logging")
        UiLogMessageHandler.logging_enabled = False
        message = ZynthianWebSocketMessage('UiLogMessageHandler', 'Restarting UI in normal mode')
        self.websocket.write_message(jsonpickle.encode(message))
        if UiLogMessageHandler.logging_thread:
            UiLogMessageHandler.logging_thread.stop()

        self.toggle_service("zynthian_debug", "zynthian")

        self.spawn_tail_thread(False)

    def on_websocket_message(self, action):
        logging.debug("action: %s " % action)
        if action == 'SHOW_DEBUG_LOGGING':
            self.do_start_debug_logging()
        elif action == 'HIDE_DEBUG_LOGGING':
            self.do_stop_debug_logging()
        elif action == 'SHOW_DEFAULT':
            if UiLogMessageHandler.logging_thread:
                UiLogMessageHandler.logging_thread.stop()
            self.spawn_tail_thread(False)
        logging.debug("message handled.")  # this needs to show up early to get the socket working again.

    def on_close(self):
        logging.debug("stopping tail threads")
        if UiLogMessageHandler.logging_thread:
            UiLogMessageHandler.logging_thread.stop()






