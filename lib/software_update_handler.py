# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Software Update Handler
#
# Copyright (C) 2017 Markus Heidt <markus@heidt-tech.com>
#
# ********************************************************************
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

import os
import logging
import asyncio
from time import monotonic
from subprocess import Popen, DEVNULL

import tornado.web
import tornado.websocket
from collections import OrderedDict
import jsonpickle
from lib.zynthian_config_handler import ZynthianBasicHandler
from lib.zynthian_websocket_handler import ZynthianWebSocketMessageHandler, ZynthianWebSocketMessage

ZYNTHIAN_SYS_DIR = os.environ.get("ZYNTHIAN_SYS_DIR", "/zynthian/zynthian-sys")

UPDATE_COMMANDS = OrderedDict([
    # ['Diagnosis', 'echo "Not implemented yet"'],
    # ['Reset to Factory Settings', 'echo "Not implemented yet"'],
    ['Update Software', f"{ZYNTHIAN_SYS_DIR}/scripts/update_zynthian.sh"]
]
)

# The update runs as a separate service (zynthian-update). These are written by its scripts.
UPDATE_LOG = "/tmp/zynthian_update.log"
UPDATE_RUNNING_FILE = "/run/zynthian_update/running"
# Message asking to show the progress of a running update, without starting one
FOLLOW_COMMAND = "__FOLLOW__"
# Message asking for the log of the last update
LAST_LOG_COMMAND = "__LAST_LOG__"


def update_running():
    return os.path.isfile(UPDATE_RUNNING_FILE)

# ------------------------------------------------------------------------------
# SoftwareUpdateHandler Config Handler
# ------------------------------------------------------------------------------


class SoftwareUpdateHandler(ZynthianBasicHandler):

    @tornado.web.authenticated
    def get(self, errors=None):
        config = OrderedDict([])
        config['UPDATE_COMMANDS'] = UPDATE_COMMANDS.keys()
        config['UPDATE_RUNNING'] = update_running()
        super().get("update.html", "Software Update", config, errors)


class SoftwareUpdateMessageHandler(ZynthianWebSocketMessageHandler):
    @classmethod
    def is_registered_for(cls, handler_name):
        return handler_name == 'SoftwareUpdateMessageHandler'

    def send(self, text):
        """Send a message to the page. Returns False if the websocket is closed."""
        try:
            message = ZynthianWebSocketMessage('SoftwareUpdateMessageHandler', text)
            self.websocket.write_message(jsonpickle.encode(message))
            return True
        except tornado.websocket.WebSocketClosedError:
            return False

    def on_websocket_message(self, update_command):
        proc = None
        if update_command == LAST_LOG_COMMAND and not update_running():
            try:
                with open(UPDATE_LOG, "r", errors="replace") as f:
                    for line in f.read().split("\n"):
                        if line.strip() != "EOUPDATE":
                            self.send(line)
            except OSError:
                pass
            self.send("EOCOMMAND")
            return
        if update_command in (FOLLOW_COMMAND, LAST_LOG_COMMAND):
            # Page opened: show the progress of a running update (started from anywhere)
            if not update_running():
                self.send("EOCOMMAND")
                return
        elif not update_running():
            try:
                # Not waited for: the update follows the log, below. The update script
                # runs the update in a separate service, so it survives webconf restarts.
                proc = Popen(UPDATE_COMMANDS[update_command], shell=True, stdout=DEVNULL,
                             stderr=DEVNULL, start_new_session=True)
            except Exception as e:
                logging.error(f"Can't start '{update_command}': {e}")
                self.send(f"ERROR: Can't start '{update_command}': {e}")
                self.send("EOCOMMAND")
                return
        # Follow the update log without blocking webconf
        self.ioloop.create_task(self.follow_update(proc))

    async def follow_update(self, proc=None):
        # Wait for the update to start: the log is truncated before the running flag is set
        deadline = monotonic() + 30
        while not update_running():
            if monotonic() > deadline or (proc and proc.poll() is not None and not update_running()):
                self.send("ERROR: The update didn't start.")
                self.send("EOCOMMAND")
                return
            await asyncio.sleep(0.2)

        pos = 0
        partial = ""
        while True:
            running = update_running()
            try:
                if os.path.getsize(UPDATE_LOG) < pos:
                    pos = 0
                with open(UPDATE_LOG, "r", errors="replace") as f:
                    f.seek(pos)
                    data = f.read()
                    pos = f.tell()
            except OSError:
                data = ""
            if data:
                lines = (partial + data).split("\n")
                partial = lines.pop()
                for line in lines:
                    if line.strip() == "EOUPDATE":
                        continue
                    if not self.send(line):
                        return
            if not running:
                break
            await asyncio.sleep(0.5)
            if proc:
                proc.poll()  # Reap the launcher when it ends
        if partial:
            self.send(partial)
        self.send("EOCOMMAND")
