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
import time
import asyncio
import subprocess
import jsonpickle
import tornado.web
from collections import OrderedDict
from multiprocessing import Queue
from subprocess import check_output
from lib.tail_thread import TailThread, AsynchronousFileReader

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
			self.render("config.html", body="ui_log.html", config=config, title="UI Log", errors=errors)


	@tornado.web.authenticated
	def post(self):
		self.get()


class UiTailThread(TailThread):

	def __init__(self, websocket, loop, process_command):
		TailThread.__init__(self, websocket, loop)
		self.process_command = process_command
		self.loop = loop


	def run(self):
		asyncio.set_event_loop(self.loop)
		process = subprocess.Popen(self.process_command, shell=True, stderr=subprocess.PIPE,
				stdout=subprocess.PIPE)

		stdout_queue = Queue()
		stdout_reader = AsynchronousFileReader(process.stdout, stdout_queue)
		stdout_reader.start()
		stderr_queue = Queue()
		stderr_reader = AsynchronousFileReader(process.stderr, stderr_queue)
		stderr_reader.start()

		while self.is_running and (not stdout_reader.eof() or not stderr_reader.eof()):
			while self.is_running and not stdout_queue.empty() and not stdout_reader.eof():
				line = stdout_queue.get()
				logging.info("stdout: %s" % line.decode())
				message = ZynthianWebSocketMessage('UiLogMessageHandler', line.decode())
				self.websocket.write_message(jsonpickle.encode(message))

			while self.is_running and not stderr_queue.empty() and not stderr_reader.eof():
				line = stderr_queue.get()
				logging.info("stderr: %s" % line.decode())
				message = ZynthianWebSocketMessage('UiLogMessageHandler', line.decode())
				self.websocket.write_message(jsonpickle.encode(message))

		stdout_reader.join()
		stderr_reader.join()
		process.stdout.close()
		process.stderr.close()


class UiLogMessageHandler(ZynthianWebSocketMessageHandler):
	logging_thread = None


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
		UiLogMessageHandler.logging_thread = UiTailThread(self.websocket, loop, self.get_process_command(debug_level))
		UiLogMessageHandler.logging_thread.start()


	def toggle_service(self, running_service, next_service):
		check_output("(systemctl stop %s)&" % running_service, shell=True)

		is_active = True
		max_trials = 20
		while is_active and max_trials > 0:
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
			max_trials -= 1

		check_output("(systemctl start %s)&" % next_service, shell=True)


	def do_start_debug_logging(self):
		logging.info("start debug logging")
		message = ZynthianWebSocketMessage('UiLogMessageHandler', 'Restarting UI in debug mode')
		self.websocket.write_message(jsonpickle.encode(message))
		if UiLogMessageHandler.logging_thread:
			UiLogMessageHandler.logging_thread.stop()

		self.toggle_service("zynthian", "zynthian_debug")

		self.spawn_tail_thread(True)


	def do_stop_debug_logging(self):
		logging.info("stop debug logging")
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

