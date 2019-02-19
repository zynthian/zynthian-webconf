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
import logging
import tornado.web
import json
import requests
import subprocess
import shlex
import shutil
import glob
from subprocess import check_output
from collections import OrderedDict
from xml.etree import ElementTree as ET

from lib.zynthian_config_handler import ZynthianConfigHandler
from zyngine.zynthian_engine_pianoteq import *

#------------------------------------------------------------------------------
# Soundfont Configuration
#------------------------------------------------------------------------------

class PianoteqHandler(ZynthianConfigHandler):

	data_dir = os.environ.get('ZYNTHIAN_DATA_DIR',"/zynthian/zynthian-data")
	plugins_dir = os.environ.get('ZYNTHIAN_PLUGINS_DIR',"/zynthian/zynthian-plugins")
	recipes_dir = os.environ.get('ZYNTHIAN_RECIPE_DIR',"/zynthian/zynthian-sys/scripts/recipes")

	@tornado.web.authenticated
	def get(self, errors=None):
		#self.pianoteq_autoconfig()
		config=OrderedDict([])
		config['ZYNTHIAN_UPLOAD_MULTIPLE'] = False
		config['ZYNTHIAN_PIANOTEQ_TRIAL'] = PIANOTEQ_TRIAL
		config['ZYNTHIAN_PIANOTEQ_VERSION'] = ".".join(str(v) for v in PIANOTEQ_VERSION)
		config['ZYNTHIAN_PIANOTEQ_PRODUCT'] = PIANOTEQ_PRODUCT
		config['ZYNTHIAN_PIANOTEQ_LICENSE'] = self.get_license_key()
		if self.genjson:
			self.write(config)
		else:
			if errors:
				logging.error("Pianoteq Action Failed: %s" % format(errors))
				self.clear()
				self.set_status(400)
				self.finish("Pianoteq Action Failed: %s" % format(errors))
			else:
				self.render("config.html", body="pianoteq.html", config=config, title="Pianoteq", errors=errors)


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
		filename = self.get_argument('ZYNTHIAN_PIANOTEQ_FILENAME');
		if filename:
			logging.info("Installing %s" % filename)

			# Install different type of files
			filename_parts = os.path.splitext(filename)
			# Pianoteq binaries
			if filename_parts[1].lower() == '.7z':
				errors = self.do_install_pianoteq_binary(filename);
			# Pianoteq instruments
			elif filename_parts[1].lower() == '.ptq':
				errors = self.do_install_pianoteq_ptq(filename);

			# Configure Pianoteq
			self.pianoteq_autoconfig()

		else:
			errors = 'Please, select a file'

		return errors


	def do_install_pianoteq_binary(self, filename):
		# Install new binary package
		command = self.recipes_dir + "/install_pianoteq_binary.sh {}".format(filename)
		check_output(command, shell=True)


	def do_install_pianoteq_ptq(self, filename):
		# Create "Addons" directory if not already exist
		if not os.path.isdir(PIANOTEQ_ADDON_DIR):
			os.makedirs(PIANOTEQ_ADDON_DIR)

		logging.info("Moving %s to %s" % (filename, PIANOTEQ_ADDON_DIR))
		shutil.move(filename, PIANOTEQ_ADDON_DIR + "/" + os.path.basename(filename))


	def do_activate_license(self):
		license_serial = self.get_argument('ZYNTHIAN_PIANOTEQ_LICENSE');
		logging.info("Configuring Pianoteq License Key: {}".format(license_serial))
		
		# Activate the License Key by calling Pianoteq binary
		command = "{} --activate {}".format(PIANOTEQ_BINARY, license_serial)
		result = check_output(command, shell=True).decode("utf-8")
		if result != "Activation Key Saved !\n":
			logging.error("Pianoteq License Activation Failed: {}".format(result))
			return result


	def do_update_presets_cache(self):
		zynthian_engine_pianoteq(None, True)


	def get_license_key(self):
		#xpath with fromstring doesn't work
		if os.path.exists(PIANOTEQ_ADDON_DIR):
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
				"PIANOTEQ_PRODUCT": [str(info['product'])],
				"PIANOTEQ_VERSION": [str(info['version'])],
				"PIANOTEQ_TRIAL": [str(info['trial'])]
			}
			errors=self.update_config(config)

		# Regenerate presets cache
		zynthian_engine_pianoteq(None, True)
