# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Reboot Handler
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

from lib.zynthian_config_handler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# Reboot Handler
#------------------------------------------------------------------------------



class RebootHandler(ZynthianConfigHandler):

	@tornado.web.authenticated
	def get(self):
		self.render("config.html", body="reboot_confirm_block.html", config=None, title="Reboot", errors=None)

	def post(self):
		if self.genjson:
			self.write("REBOOT")
		else:
			self.render("config.html", body="reboot_block.html", config=None, title="Reboot", errors=None)
		try:
			check_output("(sleep 1 & reboot)&", shell=True)
		except Exception as e:
			logging.error(e)
