#!/usr/bin/python3
# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Web Service API
#
# Copyright (C) 2015-2017 Fernando Moyano <jofemodo@zynthian.org>
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
import sys
import string
import random
import logging
import tornado.web
import tornado.ioloop

from lib.login_handler import LoginHandler
from lib.dashboard_handler import DashboardHandler
from lib.audio_config_handler import AudioConfigHandler
from lib.display_config_handler import DisplayConfigHandler
from lib.reboot_handler import RebootHandler
from lib.poweroff_handler import PoweroffHandler
from lib.security_config_handler import SecurityConfigHandler
from lib.ui_config_handler import UiConfigHandler
from lib.wiring_config_handler import WiringConfigHandler
from lib.wifi_config_handler import WifiConfigHandler
from lib.wifi_list_handler import WifiListHandler
from lib.snapshot_config_handler import SnapshotConfigHandler
from lib.midi_config_handler import MidiConfigHandler
from lib.soundfont_config_handler import SoundfontConfigHandler
from lib.upload_handler import UploadHandler
from lib.system_backup_handler import SystemBackupHandler
from lib.software_update_handler import SoftwareUpdateHandler
from lib.presets_config_handler import PresetsConfigHandler
from lib.zynthian_websocket_handler import ZynthianWebSocketHandler
from lib.pianoteq_handler import PianoteqHandler
from lib.captures_config_handler import CapturesConfigHandler
from lib.jalv_lv2_handler import JalvLv2Handler
from lib.ui_log_handler import UiLogHandler
from lib.midi_log_handler import MidiLogHandler

#------------------------------------------------------------------------------

MB = 1024 * 1024
GB = 1024 * MB
TB = 1024 * GB
MAX_STREAMED_SIZE = 1*TB

#------------------------------------------------------------------------------
# Configure Logging
#------------------------------------------------------------------------------

if os.environ.get('ZYNTHIAN_WEBCONF_LOG_LEVEL'):
	log_level=int(os.environ.get('ZYNTHIAN_WEBCONF_LOG_LEVEL'))
else:
	log_level=logging.ERROR
	#log_level=logging.WARNING

# Set root logging level
logging.basicConfig(stream=sys.stderr, level=log_level)


#------------------------------------------------------------------------------
# Build Web App & Start Server
#------------------------------------------------------------------------------

# Try to load from config file. If doesn't exist, generate a new one and save it!
def get_cookie_secret():
	cookie_secret_fpath="%s/webconf_cookie_secret.txt" % os.environ.get('ZYNTHIAN_CONFIG_DIR')
	try:
		with open(cookie_secret_fpath, "r") as fh:
			cookie_secret = fh.read().strip()
			#logging.info("Cookie Secret: %s" % cookie_secret)
			return cookie_secret
	except:
		cookie_secret = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(37))
		logging.info("Generated new Cookie Secret: %s" % cookie_secret)
		try:
			with open(cookie_secret_fpath, "w") as fh:
				fh.write(cookie_secret)
				fh.flush()
				os.fsync(fh.fileno())
		except Exception as e:
			logging.error("Can't save cookie secret file '%s': %s" % (cookie_secret_fpath,e))
		return cookie_secret


def make_app():

	settings = {
		"template_path": "templates",
		"cookie_secret": get_cookie_secret(),
		"login_url": "/login",
		"upload_progress_handler": dict()
	}

	return tornado.web.Application([
		(r'/$', DashboardHandler),
		#(r'/()$', tornado.web.StaticFileHandler, {'path': 'html', "default_filename": "index.html"}),
		(r'/(.*\.html)$', tornado.web.StaticFileHandler, {'path': 'html'}),
		(r'/(favicon\.ico)$', tornado.web.StaticFileHandler, {'path': 'img'}),
		(r'/fonts/(.*)$', tornado.web.StaticFileHandler, {'path': 'fonts'}),
		(r'/img/(.*)$', tornado.web.StaticFileHandler, {'path': 'img'}),
		(r'/css/(.*)$', tornado.web.StaticFileHandler, {'path': 'css'}),
		(r'/js/(.*)$', tornado.web.StaticFileHandler, {'path': 'js'}),
		(r'/bower_components/(.*)$', tornado.web.StaticFileHandler, {'path': 'bower_components'}),
		(r"/login", LoginHandler),
		(r"/api/lib-snapshot$", SnapshotConfigHandler),
		(r"/api/lib-soundfont$", SoundfontConfigHandler),
		(r"/api/lib-presets$", PresetsConfigHandler),
		(r"/api/lib-captures$", CapturesConfigHandler),
		(r"/api/hw-audio$", AudioConfigHandler),
		(r"/api/hw-display$", DisplayConfigHandler),
		(r"/api/hw-wiring$", WiringConfigHandler),
		(r"/api/sw-update$", SoftwareUpdateHandler),
		(r"/api/sw-pianoteq$", PianoteqHandler),
		(r"/api/sw-jalv-lv2$", JalvLv2Handler),
		(r"/api/ui-options$", UiConfigHandler),
		(r"/api/ui-log$", UiLogHandler),
		(r"/api/ui-midi-options$", MidiConfigHandler),
		(r"/api/ui-midi-log$", MidiLogHandler),
		(r"/api/sys-wifi$", WifiConfigHandler),
		(r"/api/sys-backup$", SystemBackupHandler),
		(r"/api/sys-security$", SecurityConfigHandler),
		(r"/api/sys-reboot$", RebootHandler),
		(r"/api/sys-poweroff$", PoweroffHandler),
		(r"/api/wifi/list$", WifiListHandler),
		(r'/api/upload$', UploadHandler),
		(r"/api/ws$", ZynthianWebSocketHandler),
	], **settings)


if __name__ == "__main__":
	app = make_app()
	app.listen(os.environ.get('ZYNTHIAN_WEBCONF_PORT', 80), max_body_size=MAX_STREAMED_SIZE)
	tornado.ioloop.IOLoop.current().start()

#------------------------------------------------------------------------------
