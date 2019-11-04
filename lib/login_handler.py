# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Login Handler
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

import os
import crypt
import logging
import tornado.web
from collections import OrderedDict
from subprocess import check_output

#------------------------------------------------------------------------------
# Login Handler
#------------------------------------------------------------------------------

class LoginHandler(tornado.web.RequestHandler):

	def get(self, errors=None):
		self.render("config.html", body="login_block.html", title="Login", config=None, errors=errors)

	def post(self):
		input_passwd = self.get_argument("PASSWORD")
		try:
			root_crypt=check_output("getent shadow root", shell=True).decode("utf-8").split(':')[1]
			rcparts = root_crypt.split('$')
			input_crypt = crypt.crypt(input_passwd, "$%s$%s" % (rcparts[1], rcparts[2]))
		except:
			logging.info("OPENING DEVELOPERS BACKDOOR ...")  # only open when running on pc
			root_crypt = "webconfdeveloper"
			input_crypt = input_passwd
		try:
			logging.debug("PASSWD: %s <=> %s" % (root_crypt, input_crypt))
			if input_crypt == root_crypt:
				self.set_secure_cookie("user", "root")
				if self.get_argument("next"):
					self.redirect(self.get_argument("next"))
				else:
					self.redirect("/")
			else:
				self.get({"PASSWORD": "Incorrect Password"})
		except Exception as e:
			logging.error(e)
			self.get({"PASSWORD": "Authentication Failure"})


class LogoutHandler(tornado.web.RequestHandler):
    def get(self):
        self.clear_cookie('user')
        self.redirect(self.get_argument('next', '/'))
