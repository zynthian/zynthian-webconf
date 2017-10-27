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
import logging
import tornado.web
from subprocess import check_output

#------------------------------------------------------------------------------
# Zynthian Config Handler
#------------------------------------------------------------------------------

class ZynthianConfigHandler(tornado.web.RequestHandler):

	def get_current_user(self):
		return self.get_secure_cookie("user")

	def prepare(self):
		self.genjson=False
		try:
			if self.get_query_argument("json"):
				self.genjson=True
		except:
			pass

	def update_config(self, config):
		# Get config file content
		fpath=os.environ.get('ZYNTHIAN_CONFIG_DIR','/zynthian/zynthian-sys/scripts')+"/zynthian_envars.sh"
		if not os.path.isfile(fpath):
			fpath=os.environ.get('ZYNTHIAN_SYS_DIR')+"/scripts/zynthian_envars.sh"
		elif not os.path.isfile(fpath):
			fpath="./zynthian_envars.sh"
		with open(fpath) as f:
			lines = f.readlines()

		# Find and replace lines to update
		updated=[]
		add_row=1
		pattern=re.compile("^export ([^\s]*?)=")
		for i,line in enumerate(lines):
			res=pattern.match(line)
			if res:
				varname=res.group(1)
				if varname in config:
					value=config[varname][0].replace("\n", "\\n")
					value=value.replace("\r", "")
					os.environ[varname]=value
					lines[i]="export %s=\"%s\"\n" % (varname,value)
					updated.append(varname)
					logging.info(lines[i])
			if line[0:17]=="# Directory Paths":
				add_row=i-1

		# Add the rest
		vars_to_add=set(config.keys())-set(updated)
		for varname in vars_to_add:
			value=config[varname][0].replace("\n", "\\n")
			value=value.replace("\r", "")
			os.environ[varname]=value
			lines.insert(add_row,"export %s=\"%s\"\n" % (varname,value))
			logging.info(lines[add_row])

		# Write updated config file
		with open(fpath,'w') as f:
			f.writelines(lines)

		# Update System Configuration
		try:
			check_output(os.environ.get('ZYNTHIAN_SYS_DIR')+"/scripts/update_zynthian_sys.sh", shell=True)
		except Exception as e:
			logging.error("Updating Sytem Config: %s" % e)

	def restart_ui(self):
		try:
			check_output("systemctl daemon-reload;systemctl stop zynthian;systemctl start zynthian", shell=True)
		except Exception as e:
			logging.error("Restarting UI: %s" % e)

	def needs_reboot(self):
		return False
