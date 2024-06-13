# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Login Handler
#
# Copyright (C) 2017 Fernando Moyano <jofemodo@zynthian.org>
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
import PAM
import logging
import tornado.web

# ------------------------------------------------------------------------------
# Login Handler
# ------------------------------------------------------------------------------


class LoginHandler(tornado.web.RequestHandler):

	def get(self, errors=None):
		self.render("config.html", info={}, body="login_block.html", title="Login", config=None, errors=errors)

	def post(self):
		def pam_conv(auth, query_list, userData):
			resp = []
			for i in range(len(query_list)):
				query, type = query_list[i]
				if type in (PAM.PAM_PROMPT_ECHO_ON, PAM.PAM_PROMPT_ECHO_OFF):
					val = self.get_argument("PASSWORD")
					resp.append((val, 0))
				elif type == PAM.PAM_PROMPT_ERROR_MSG or type == PAM.PAM_PROMPT_TEXT_INFO:
					logging.error(query)
					resp.append(('', 0))
				else:
					return None
			return resp

		auth = PAM.pam()
		auth.start("passwd")
		auth.set_item(PAM.PAM_USER, "root")
		auth.set_item(PAM.PAM_CONV, pam_conv)
		try:
			auth.authenticate()
			auth.acct_mgmt()
		except PAM.error as resp:
			logging.info(f"Incorrect password => {resp}")
			self.get({"PASSWORD": "Incorrect Password"})
		except Exception as e:
			logging.error(e)
			self.get({"PASSWORD": "Authentication Failure"})
		else:
			self.set_secure_cookie("user", "root", expires_days=3650)
			if self.get_argument("next", ""):
				self.redirect(self.get_argument("next"))
			else:
				self.redirect("/")


class LogoutHandler(tornado.web.RequestHandler):
	def get(self):
		self.clear_cookie('user')
		self.redirect(self.get_argument('next', '/'))

