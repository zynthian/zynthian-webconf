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

import time
import logging
from concurrent.futures import ThreadPoolExecutor

import tornado.web
from subprocess import check_output
import subprocess
import jsonpickle
from collections import OrderedDict
import threading
from multiprocessing import Queue
from tornado.concurrent import run_on_executor
import concurrent.futures
import asyncio

#in case the blocking process.stdout.readline() is an issue:
#https://www.stefaanlippens.net/python-asynchronous-subprocess-pipe-reading/
from tornado.ioloop import IOLoop

from lib.zynthian_websocket_handler import ZynthianWebSocketMessageHandler, ZynthianWebSocketMessage

def message_processed_callback(future):
    logging.info('Callsback(future=%r)' % ( future))

#------------------------------------------------------------------------------
# UI Configuration
#------------------------------------------------------------------------------

class UiLogHandler(tornado.web.RequestHandler):


	def get_current_user(self):
		return self.get_secure_cookie("user")


	def prepare(self):
		self.genjson=False
		try:
			if self.get_query_argument("json"):
				self.genjson=True
		except:
			pass

	@tornado.web.authenticated
	def get(self, errors=None):
		config=OrderedDict([])
		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="ui_log.html", config=config, title="UI Log", errors=errors)

	@tornado.web.authenticated
	def post(self):

		self.get()



class UiLogMessageHandler(ZynthianWebSocketMessageHandler):
    executor = ThreadPoolExecutor(max_workers=10)
    logging_enabled = False

    @classmethod
    def is_registered_for(cls, handler_name):
        return handler_name == 'UiLogMessageHandler'

    @run_on_executor
    def background_task(self,  process):
        while UiLogMessageHandler.logging_enabled:
            logging.info("while process.stdout.readline()")
            line = process.stdout.readline()
            if line:
                logging.info(line.decode())

                message = ZynthianWebSocketMessage('UiLogMessageHandler', line.decode())
                try:
                    self.websocket.write_message(jsonpickle.encode(message))
                except Exception as e:
                    # I can't fix the  "This event loop is already running" and There is no current event loop in thread 'ThreadPoolExecutor-0_0'
                    logging.error(e)
            asyncio.sleep(1)

    @tornado.gen.coroutine
    def do_start_logging(self):
        logging.info("start ui logging")
        UiLogMessageHandler.logging_enabled = True
        message = ZynthianWebSocketMessage('UiLogMessageHandler', 'Restarting UI in debug mode')
        self.websocket.write_message(jsonpickle.encode(message))

        check_output("(systemctl stop zynthian & sleep 1 & systemctl restart zynthian_debug & sleep 1 )&", shell=True)

        process = subprocess.Popen('journalctl -f -u zynthian_debug', shell=True, stderr=subprocess.PIPE,
                                  stdout=subprocess.PIPE)

        logging.info("before run_until_complete")

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.background_task(process))


        logging.info('after run_until_complete')




    def do_stop_logging(self):
        logging.info("stop ui logging")
        UiLogMessageHandler.logging_enabled = False
        message = ZynthianWebSocketMessage('UiLogMessageHandler', 'Restarting UI in normal mode')
        self.websocket.write_message(jsonpickle.encode(message))
        check_output("(systemctl stop zynthian_debug & sleep 10 & systemctl start zynthian)&", shell=True)

    def on_websocket_message(self, action):
        logging.info(action)
        if action == 'START':
            self.do_start_logging()
            logging.info("after do_start_logging")


        else:
            self.do_stop_logging()
        logging.info("message handled.")  # this needs to show up early to get the socket working again.




