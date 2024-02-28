# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Zynterm Handler
#
# Copyright (C) 2020 Fernando Moyano <jofemodo@zynthian.org>
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

import logging
import tornado.web

from lib.zynthian_config_handler import ZynthianBasicHandler

# ------------------------------------------------------------------------------
# Zynterm Handler
# ------------------------------------------------------------------------------


class ZyntermHandler(ZynthianBasicHandler):

	@tornado.web.authenticated
	def get(self):
		config = {
			"xstatic": self.application.settings['xstatic_url'],
			"ws_url_path": "/zynterm_ws"
		}
		super().get("zynterm.html", "Terminal", config, None)
