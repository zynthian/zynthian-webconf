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
from subprocess import check_output
import subprocess
import jsonpickle
from collections import OrderedDict
import threading
from multiprocessing import Queue

import asyncio

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


class TailThread(threading.Thread):
    def __init__(self, websocket, loop):
        super(TailThread, self).__init__()
        self.is_logging = True
        self.websocket = websocket
        self.loop = loop

    def stop(self):
        self.is_logging = False

    def run(self):
        process = subprocess.Popen('journalctl  -f -u zynthian_debug', shell=True, stderr=subprocess.PIPE,
                                   stdout=subprocess.PIPE)

        stdout_queue = Queue()
        stdout_reader = AsynchronousFileReader(process.stdout, stdout_queue)
        stdout_reader.start()
        stderr_queue = Queue()
        stderr_reader = AsynchronousFileReader(process.stderr, stderr_queue)
        stderr_reader.start()
        asyncio.set_event_loop(self.loop)


        while self.is_logging and (not stdout_reader.eof() or not stderr_reader.eof()):
            while not stdout_queue.empty():
                line = stdout_queue.get()
                logging.info(line.decode())

                message = ZynthianWebSocketMessage('UiLogMessageHandler', line.decode())
                self.websocket.write_message(jsonpickle.encode(message))
            while not stderr_queue.empty():
                line = stderr_queue.get()
                logging.info(line.decode())

                message = ZynthianWebSocketMessage('UiLogMessageHandler', line.decode())
                self.websocket.write_message(jsonpickle.encode(message))

        stdout_reader.join()
        stderr_reader.join()
        process.stdout.close()
        process.stderr.close()


class UiLogMessageHandler(ZynthianWebSocketMessageHandler):
    logging_thread = None
    is_logging = True

    @classmethod
    def is_registered_for(cls, handler_name):
        return handler_name == 'UiLogMessageHandler'

    def do_start_logging(self):
        logging.info("start ui logging")
        UiLogMessageHandler.logging_enabled = True
        message = ZynthianWebSocketMessage('UiLogMessageHandler', 'Restarting UI in debug mode')
        self.websocket.write_message(jsonpickle.encode(message))

        check_output("(systemctl stop zynthian & sleep 5 & systemctl restart zynthian_debug)&", shell=True)

        logging.info("before starting tail thread")
        loop = asyncio.get_event_loop()
        UiLogMessageHandler.logging_thread = TailThread(self.websocket, loop)
        UiLogMessageHandler.logging_thread.start()

        logging.info('after run_until_complete')

    def do_stop_logging(self):
        logging.info("stop ui logging")
        UiLogMessageHandler.logging_enabled = False
        message = ZynthianWebSocketMessage('UiLogMessageHandler', 'Restarting UI in normal mode')
        self.websocket.write_message(jsonpickle.encode(message))
        check_output("(systemctl stop zynthian_debug & sleep 5 & systemctl start zynthian)&", shell=True)
        if UiLogMessageHandler.logging_thread:
            UiLogMessageHandler.logging_thread.stop()
            UiLogMessageHandler.logging_thread = None

    def on_websocket_message(self, action):
        logging.info(action)
        if action == 'START':
            self.do_start_logging()
            logging.info("after do_start_logging")
        else:
            self.do_stop_logging()
        logging.info("message handled.")  # this needs to show up early to get the socket working again.


class AsynchronousFileReader(threading.Thread):
    '''
    Helper class to implement asynchronous reading of a file
    in a separate thread. Pushes read lines on a queue to
    be consumed in another thread.
    '''

    def __init__(self, fd, queue):
        assert callable(fd.readline)
        threading.Thread.__init__(self)
        self._fd = fd
        self._queue = queue

    def run(self):
        '''The body of the tread: read lines and put them on the queue.'''
        for line in iter(self._fd.readline, ''):
            self._queue.put(line)

    def eof(self):
        '''Check whether there is no more content to expect.'''
        return not self.is_alive() and self._queue.empty()



