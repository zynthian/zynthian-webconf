# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Presets Manager Handler
#
# Copyright (C) 2017 Markus Heidt <markus@heidt-tech.com>
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
import logging
import tornado.web
import shutil
from subprocess import check_output, STDOUT
from collections import OrderedDict
from xml.etree import ElementTree as ET

from lib.zynthian_config_handler import ZynthianBasicHandler
from zyngine.zynthian_engine_pianoteq import *
from zyngine.zynthian_engine_pianoteq6 import zynthian_engine_pianoteq6

sys.path.append(os.environ.get('ZYNTHIAN_UI_DIR'))
import zynconf

#------------------------------------------------------------------------------
# Soundfont Configuration
#------------------------------------------------------------------------------

class PianoteqHandler(ZynthianBasicHandler):

	data_dir = os.environ.get('ZYNTHIAN_DATA_DIR',"/zynthian/zynthian-data")
	plugins_dir = os.environ.get('ZYNTHIAN_PLUGINS_DIR',"/zynthian/zynthian-plugins")
	recipes_dir = os.environ.get('ZYNTHIAN_RECIPE_DIR',"/zynthian/zynthian-sys/scripts/recipes")

	@tornado.web.authenticated
	def get(self, errors=None):
		#self.pianoteq_autoconfig()
		config=OrderedDict([])
		info = get_pianoteq_binary_info()
		config['ZYNTHIAN_UPLOAD_MULTIPLE'] = False
		config['ZYNTHIAN_PIANOTEQ_TRIAL'] = info['trial']
		config['ZYNTHIAN_PIANOTEQ_VERSION'] = info['version_str']
		config['ZYNTHIAN_PIANOTEQ_PRODUCT'] = info['product']
		config['ZYNTHIAN_PIANOTEQ_LICENSE'] = self.get_license_key()

		if errors:
			logging.error("Pianoteq Action Failed: %s" % format(errors))
		super().get("pianoteq.html", "Pianoteq", config, errors)


	@tornado.web.authenticated
	def post(self):
		action = self.get_argument('ZYNTHIAN_PIANOTEQ_ACTION')
		if action:
			errors = {
				'INSTALL_PIANOTEQ': lambda: self.do_install_pianoteq(),
				'ACTIVATE_LICENSE': lambda: self.do_activate_license(),
				'UPDATE_PRESETS_CACHE': lambda: self.do_update_presets_cache()
			}[action]()
		self.get(errors)


	def do_install_pianoteq(self):
		errors = None
		filename = self.get_argument('ZYNTHIAN_PIANOTEQ_FILENAME')
		if filename:
			logging.info("Installing %s" % filename)

			# Install different type of files
			filename_parts = os.path.splitext(filename)
			# Pianoteq binaries
			if filename_parts[1].lower() == '.7z':
				errors = self.do_install_pianoteq_binary(filename)
			# Pianoteq instruments
			elif filename_parts[1].lower() == '.ptq':
				errors = self.do_install_pianoteq_ptq(filename)

			# Configure Pianoteq
			self.pianoteq_autoconfig()

		else:
			errors = 'Please, select a file'

		return errors


	def do_install_pianoteq_binary(self, filename):
		# Install new binary package
		command = self.recipes_dir + "/install_pianoteq_binary.sh {}; exit 0".format(filename)
		result = check_output(command, shell=True, stderr=STDOUT).decode("utf-8")
		# TODO! if result is OK, return None!
		return result


	def do_install_pianoteq_ptq(self, filename):
		try:
			# Create "Addons" directory if not already exist
			if not os.path.isdir(PIANOTEQ_ADDON_DIR):
				os.makedirs(PIANOTEQ_ADDON_DIR)
			# Copy uploaded file
			logging.info("Moving %s to %s" % (filename, PIANOTEQ_ADDON_DIR))
			shutil.move(filename, PIANOTEQ_ADDON_DIR + "/" + os.path.basename(filename))
		except Exception as e:
			logging.error("PTQ install failed: {}".format(e))
			return "PTQ install failed: {}".format(e)


	def do_activate_license(self):
		license_serial = self.get_argument('ZYNTHIAN_PIANOTEQ_LICENSE')
		logging.info("Configuring Pianoteq License Key: {}".format(license_serial))
		
		# Activate the License Key by calling Pianoteq binary
		command = "{} --prefs {} --activate {}; exit 0".format(PIANOTEQ_BINARY, PIANOTEQ_CONFIG_FILE, license_serial)
		try:
			result = check_output(command, shell=True, stderr=STDOUT).decode("utf-8")
		except Exception as e:
			logging.error(format(e))
			result = format(e)

		if result != "Activation Key Saved !\n":
			logging.error(result)
			return result
		else:
			self.pianoteq_autoconfig()


	def do_update_presets_cache(self):
		zynthian_engine_pianoteq6(None, True)


	def get_license_key(self):
		#xpath with fromstring doesn't work
		if os.path.exists(PIANOTEQ_CONFIG_FILE):
			root = ET.parse(PIANOTEQ_CONFIG_FILE)
			try:
				for xml_value in root.iter("VALUE"):
					if xml_value.attrib['name'] == 'serial':
						return xml_value.attrib['val']
			except Exception as e:
				logging.error("Error parsing license: %s" % e)


	def pianoteq_autoconfig(self):
		# Get and Save pianoteq binary options
		info = get_pianoteq_binary_info()
		if info:
			# Save envars
			config = {
				"ZYNTHIAN_PIANOTEQ_PRODUCT": [info["product"]],
				"ZYNTHIAN_PIANOTEQ_VERSION": [info["version_str"]],
				"ZYNTHIAN_PIANOTEQ_TRIAL": ["1" if info["trial"] else "0"]
			}
			self.update_config(config)

			# Regenerate presets cache
			if not info['api']:
				self.do_update_presets_cache()


	def update_config(self, config):
		sconfig={}
		for vn in config:
			sconfig[vn]=config[vn][0]

		zynconf.save_config(sconfig, updsys=True)
