# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Zynthian Configuration Handler base class
#
# Copyright (C) 2017-2024 Fernando Moyano <jofemodo@zynthian.org>
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
import liblo
import logging
import tornado.web
from time import sleep
from subprocess import check_output

import zynconf

#Avoid unwanted debug messages from zynconf module
zynconf_logger = logging.getLogger('zynconf')
zynconf_logger.setLevel(logging.INFO)

#------------------------------------------------------------------------------
# Zynthian-UI OSC Address
#------------------------------------------------------------------------------

zynthian_ui_osc_addr = liblo.Address('localhost', 1370,liblo.UDP)

#------------------------------------------------------------------------------
# Zynthian Basic Handler
#------------------------------------------------------------------------------

class ZynthianBasicHandler(tornado.web.RequestHandler):

	reboot_flag = False
	restart_ui_flag = False
	restart_webconf_flag = False
	reload_wiring_layout_flag = False
	reload_midi_config_flag = False
	reload_key_binding_flag = False

	restart_ui_flag_fpath = "/tmp/zynthian_restart_ui"
	restart_webconf_flag_fpath = "/tmp/zynthian_restart_webconf"
	reboot_flag_fpath = "/tmp/zynthian_reboot"


	def get_current_user(self):
		return self.get_secure_cookie("user", max_age_days=5200)


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


	def on_finish(self):
		if self.restart_webconf_flag:
			self.restart_webconf()


	def render(self, tpl, **kwargs):
		info = {
			'host_name': self.request.host,
			'reboot_flag': self.reboot_flag
		}

		# If MOD-UI is enabled, add access URI to info
		if self.is_service_active("mod-ui"):
			info['modui_uri']="http://{}:8888".format(self.request.host)

		# If VNC Server is enabled, add access URI to info
		if self.is_service_active("novnc0"):
			info['novnc0_uri']="http://{}:6080/vnc.html".format(self.request.host)
		if self.is_service_active("novnc1"):
			info['novnc1_uri']="http://{}:6081/vnc.html".format(self.request.host)

		# Restore scroll position
		info['scrollTop'] = int(float(self.get_argument('_scrollTop', '0')))

		super().render(tpl, info=info, **kwargs)


	@tornado.web.authenticated
	def get(self, body, title, config, errors=None):
		#logging.debug(config)

		if self.reboot_flag:
			self.persist_reboot_flag()

		if self.restart_ui_flag:
			self.restart_ui()
		else:
			if self.reload_wiring_layout_flag:
				self.reload_wiring_layout()

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


	def power_off(self):
		try:
			if self.is_service_active("zynthian"):
				liblo.send(zynthian_ui_osc_addr, "/CUIA/POWER_OFF")
				sleep(5)
			check_output("killall -SIGQUIT zynthian_gui.py; sleep 5; poweroff", shell=True)
		except Exception as e:
			logging.error("Power Off: {}".format(e))


	def reboot(self):
		try:
			self.reboot_flag = False
			if os.path.isfile(self.reboot_flag_fpath):
				os.remove(self.reboot_flag_fpath)
			if self.is_service_active("zynthian"):
				liblo.send(zynthian_ui_osc_addr, "/CUIA/REBOOT")
				sleep(5)
			check_output("killall -SIGINT zynthian_gui.py; sleep 5; reboot", shell=True)
		except Exception as e:
			logging.error("Reboot: {}".format(e))


	def restart_ui(self):
		try:
			check_output("systemctl restart zynthian", shell=True)
			self.restart_ui_flag = False
			if os.path.isfile(self.restart_ui_flag_fpath):
				os.remove(self.restart_ui_flag_fpath)
		except Exception as e:
			logging.error("Restarting UI: %s" % e)


	def restart_webconf(self):
		try:
			check_output("systemctl restart zynthian-webconf", shell=True)
			self.restart_webconf_flag = False
			if os.path.isfile(self.restart_webconf_flag_fpath):
				os.remove(self.restart_webconf_flag_fpath)
		except Exception as e:
			logging.error("Restarting Webconf: %s" % e)


	def reload_wiring_layout(self):
		liblo.send(zynthian_ui_osc_addr, "/CUIA/RELOAD_WIRING_LAYOUT")
		self.reload_wiring_layout_flag = False


	def reload_midi_config(self):
		liblo.send(zynthian_ui_osc_addr, "/CUIA/RELOAD_MIDI_CONFIG")
		self.reload_midi_config_flag = False


	def reload_key_binding(self):
		liblo.send(zynthian_ui_osc_addr, "/CUIA/RELOAD_KEY_BINDING")
		self.reload_key_binding_flag = False


	def persist_update_sys_flag(self):
		check_output("touch /zynthian_update_sys", shell=True)


	def persist_reboot_flag(self):
		check_output(f"touch {self.reboot_flag_fpath}", shell=True)


	def read_reboot_flag(self):
		self.reboot_flag = os.path.exists(self.reboot_flag_fpath)


	@classmethod
	def update_sys(cls):
		try:
			zynconf.update_sys()
			if os.path.isfile("/zynthian_update_sys"):
				os.remove("/zynthian_update_sys")
		except Exception as e:
			logging.error("Updating System Config: %s" % e)


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
			if vn[0]!='_':
				sconfig[vn]=config[vn][0]

		zynconf.save_config(sconfig, updsys=True)


	def config_env(self, config):
		for vn in config:
			if vn[0]!='_':
				os.environ[vn]=config[vn][0]

