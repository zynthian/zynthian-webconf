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
import re
import sys
import logging
import tornado.ioloop
import tornado.web
from subprocess import check_output
from collections import OrderedDict
from lib.AudioConfigHandler import AudioConfigHandler
from lib.DisplayConfigHandler import DisplayConfigHandler
from lib.RebootHandler import RebootHandler
from lib.SystemConfigHandler import SystemConfigHandler
from lib.UiConfigHandler import UiConfigHandler
from lib.WiringConfigHandler import WiringConfigHandler
from lib.WifiConfigHandler import WifiConfigHandler

#------------------------------------------------------------------------------

#Configure Logging
logging.basicConfig(filename='webconf.log', level=logging.INFO)


#------------------------------------------------------------------------------
# Build Web App & Start Server
#------------------------------------------------------------------------------

def make_app():
	return tornado.web.Application([
		(r'/$', AudioConfigHandler),
		#(r'/()$', tornado.web.StaticFileHandler, {'path': 'html', "default_filename": "index.html"}),
		(r'/(.*\.html)$', tornado.web.StaticFileHandler, {'path': 'html'}),
		(r'/(favicon\.ico)$', tornado.web.StaticFileHandler, {'path': 'img'}),
		(r'/img/(.*)$', tornado.web.StaticFileHandler, {'path': 'img'}),
		(r'/css/(.*)$', tornado.web.StaticFileHandler, {'path': 'css'}),
		(r'/js/(.*)$', tornado.web.StaticFileHandler, {'path': 'js'}),
		(r'/bower_components/(.*)$', tornado.web.StaticFileHandler, {'path': 'bower_components'}),
		(r"/api/audio$", AudioConfigHandler),
		(r"/api/display$", DisplayConfigHandler),
		(r"/api/wiring$", WiringConfigHandler),
		(r"/api/ui$", UiConfigHandler),
		(r"/api/wifi$", WifiConfigHandler),
		(r"/api/system$", SystemConfigHandler),
		(r"/api/reboot$", RebootHandler),
	], template_path="templates")

if __name__ == "__main__":
	app = make_app()
	app.listen(80)
	tornado.ioloop.IOLoop.current().start()

#------------------------------------------------------------------------------
