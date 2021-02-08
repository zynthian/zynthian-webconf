# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Zynthian Configuration Handler base class
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
import re
import sys
import liblo
import logging
import tornado.web
from subprocess import check_output

sys.path.append(os.environ.get('ZYNTHIAN_UI_DIR'))
import zynconf

#------------------------------------------------------------------------------
# Zynthian-UI OSC Address
#------------------------------------------------------------------------------

zynthian_ui_osc_addr = liblo.Address('localhost',1370,liblo.UDP)

#------------------------------------------------------------------------------
# Zynthian Basic Handler
#------------------------------------------------------------------------------

class ZynthianBasicHandler(tornado.web.RequestHandler):

	reboot_flag = False
	restart_ui_flag = False
	reload_midi_config_flag = False
	reload_key_binding_flag = False

	def get_current_user(self):
		return self.get_secure_cookie("user")


	def prepare(self):
		zynconf.load_config()
		zynconf.load_midi_config()

		self.read_reboot_flag()
		self.genjson=False
		try:
			if self.get_query_argument("json"):
				self.genjson=True
		except:
			pass


	def render(self, tpl, **kwargs):
		info = {
			'host_name': self.request.host,
			'reboot_flag': self.reboot_flag
		}

		# If MOD-UI is enabled, add access URI to info
		if self.is_service_active("mod-ui"):
			info['modui_uri']="http://{}:8888".format(self.request.host)

		# If VNC Server is enabled, add access URI to info
		if self.is_service_active("novnc"):
			info['novnc_uri']="http://{}:6080/vnc.html".format(self.request.host)

		super().render(tpl, info=info, **kwargs)


	@tornado.web.authenticated
	def get(self, body, title, config, errors=None):
		logging.debug(config)

		if self.reboot_flag:
			self.persist_reboot_flag()

		if self.restart_ui_flag:
			self.restart_ui()

		if self.reload_midi_config_flag:
			self.reload_midi_config()

		if self.reload_key_binding_flag:
			self.reload_key_binding()

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body=body, config=config, title=title, errors=errors)


	def is_service_active(self, service):
		return zynconf.is_service_active(service)


	def restart_ui(self):
		try:
			check_output("systemctl daemon-reload;systemctl restart zynthian", shell=True)
		except Exception as e:
			logging.error("Restarting UI: %s" % e)


	def reload_midi_config(self):
		liblo.send(zynthian_ui_osc_addr, "/CUIA/RELOAD_MIDI_CONFIG")


	def reload_key_binding(self):
		liblo.send(zynthian_ui_osc_addr, "/CUIA/RELOAD_KEY_BINDING")


	def persist_update_sys_flag(self):
		check_output("touch /zynthian_update_sys", shell=True)


	def persist_reboot_flag(self):
		check_output("touch /tmp/zynthian_reboot", shell=True)


	def read_reboot_flag(self):
		self.reboot_flag = os.path.exists("/tmp/zynthian_reboot")

#------------------------------------------------------------------------------
# Zynthian Config Handler
#------------------------------------------------------------------------------

class ZynthianConfigHandler(ZynthianBasicHandler):

	@tornado.web.authenticated
	def get(self, title, config, errors=None):
		super().get("config_block.html", title, config, errors)


	def update_config(self, config):
		sconfig={}
		for vn in config:
			sconfig[vn]=config[vn][0]

		zynconf.save_config(sconfig, update_sys=True)

