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
from xml.etree import ElementTree as ET
from collections import OrderedDict

from lib.zynthian_config_handler import ZynthianConfigHandler
from zyngine.zynthian_engine_pianoteq import *

#------------------------------------------------------------------------------
# Soundfont Configuration
#------------------------------------------------------------------------------

class PianoteqHandler(ZynthianConfigHandler):

	data_dir = os.environ.get('ZYNTHIAN_DATA_DIR',"/zynthian/zynthian-data")
	plugins_dir = os.environ.get('ZYNTHIAN_PLUGINS_DIR',"/zynthian/zynthian-plugins")

	@tornado.web.authenticated
	def get(self, errors=None):
		#self.pianoteq_autoconfig()
		config=OrderedDict([])
		config['ZYNTHIAN_UPLOAD_MULTIPLE'] = False
		config['ZYNTHIAN_PIANOTEQ_LICENCE'] = self.get_licence_key()
		if self.genjson:
			self.write(config)
		else:
			if errors:
				logging.error("Installing pianoteq failed: %s" % format(errors))
				self.clear()
				self.set_status(400)
				self.finish("Installing pianoteq failed: %s" % format(errors))
			else:
				self.render("config.html", body="pianoteq.html", config=config, title="Pianoteq", errors=errors)

	@tornado.web.authenticated
	def post(self):
		action = self.get_argument('ZYNTHIAN_PIANOTEQ_ACTION')
		if action:
			errors = {
				'INSTALL_PIANOTEQ': lambda: self.do_install_pianoteq(),
				'ADD_LICENCE': lambda: self.do_install_licence(),
				'UPDATE_PRESETS_CACHE': lambda: self.do_update_presets_cache()
			}[action]()
		self.get(errors)


	def do_install_licence(self):
		licence = self.get_argument('ZYNTHIAN_PIANOTEQ_LICENCE');

		logging.info(licence)
		if os.path.isfile(PIANOTEQ_CONFIG_FILE):
			root = ET.parse(PIANOTEQ_CONFIG_FILE)
			try:
				licence_value = None
				for xml_value in root.iter("VALUE"):
					logging.info(xml_value.attrib['name'])
					if xml_value.attrib['name'] == 'serial':
						licence_value = xml_value
				if licence_value is None:
					licence_value = ET.Element('VALUE')
					root.getroot().append(licence_value)
					licence_value.set('name','serial')
				licence_value.set('val', licence)
				root.write(PIANOTEQ_CONFIG_FILE)

			except Exception as e:
				logging.error("Installing licence failed: %s" % format(e))
				return format(e)

	def do_install_pianoteq(self):
		filename = self.get_argument('ZYNTHIAN_PIANOTEQ_FILENAME');
		if filename:
			logging.info("Installing %s" % filename)
			errors = None

			# Just to be sure...
			if os.path.isdir("/tmp/pianoteq"):
				shutil.rmtree("/tmp/pianoteq")
				if not os.path.isdir(PIANOTEQ_SW_DIR):
					os.mkdir(PIANOTEQ_SW_DIR)

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

			# Cover my tracks
			if(os.path.isdir("/tmp/pianoteq")):
				shutil.rmtree("/tmp/pianoteq")
		else:
			errors = 'Please select a file'
		return errors

	def do_install_pianoteq_binary(self, filename):
		# Install binary
		subprocess.call(shlex.split("/usr/bin/7z x -o/tmp/pianoteq %s \"Pianoteq 6 STAGE/arm/Pianoteq 6 STAGE*\"" % filename))
		if os.path.isfile("%s/Pianoteq 6 STAGE" % PIANOTEQ_SW_DIR):
			logging.info("Removing old pianoteq binary %s/Pianoteq 6 STAGE" % PIANOTEQ_SW_DIR)
			os.remove("%s/Pianoteq 6 STAGE" % PIANOTEQ_SW_DIR)
		logging.info("Installing new pianoteq binary")
		shutil.move("/tmp/pianoteq/Pianoteq 6 STAGE/arm/Pianoteq 6 STAGE", PIANOTEQ_SW_DIR)

		# Install LV2 plugin
		if os.path.isdir("%s/Pianoteq 6 STAGE.lv2" % PIANOTEQ_SW_DIR):
			logging.info("Removing old pianoteq LV2 plugin")
			shutil.rmtree("%s/Pianoteq 6 STAGE.lv2" % PIANOTEQ_SW_DIR)
		logging.info("Installing new pianoteq LV2 plugin")
		shutil.move("/tmp/pianoteq/Pianoteq 6 STAGE/arm/Pianoteq 6 STAGE.lv2", PIANOTEQ_SW_DIR)
		if os.path.islink(self.plugins_dir + "/lv2/Pianoteq 6 STAGE.lv2"):
			os.unlink(self.plugins_dir + "/lv2/Pianoteq 6 STAGE.lv2")
		elif os.path.isdir(self.plugins_dir + "/lv2/Pianoteq 6 STAGE.lv2"):
			shutil.rmtree(self.plugins_dir + "/lv2/Pianoteq 6 STAGE.lv2")
		elif os.path.isfile(self.plugins_dir + "/lv2/Pianoteq 6 STAGE.lv2"):
			os.remove(self.plugins_dir + "/lv2/Pianoteq 6 STAGE.lv2")
		os.symlink("%s/Pianoteq 6 STAGE.lv2" % PIANOTEQ_SW_DIR ,self.plugins_dir + "/lv2/Pianoteq 6 STAGE.lv2")

		self.recursive_copy_files(self.data_dir + "/pianoteq6/Pianoteq 6 STAGE.lv2",self.plugins_dir + "/lv2/Pianoteq 6 STAGE.lv2",True)

		# Create "My Presets" if not already exist
		if not os.path.isdir(PIANOTEQ_MY_PRESETS_DIR):
			os.makedirs(PIANOTEQ_MY_PRESETS_DIR)


	def do_install_pianoteq_ptq(self, filename):
		self.ensure_dir(PIANOTEQ_ADDON_DIR)
		logging.info("Moving %s to %s" % (filename, PIANOTEQ_ADDON_DIR))
		shutil.move(filename, PIANOTEQ_ADDON_DIR + "/" + os.path.basename(filename))

	def do_update_presets_cache(self):
		zynthian_engine_pianoteq(None, True)


	# From: https://stackoverflow.com/questions/3397752/copy-multiple-files-in-python
	def recursive_copy_files(self,source_path, destination_path, override=False):
		"""
		Recursive copies files from source  to destination directory.
		:param source_path: source directory
		:param destination_path: destination directory
		:param override if True all files will be overridden otherwise skip if file exist
		:return: count of copied files
		"""
		files_count = 0
		if not os.path.exists(destination_path):
			os.mkdir(destination_path)
		items = glob.glob(source_path + '/*')
		for item in items:
			if os.path.isdir(item):
				path = os.path.join(destination_path, item.split('/')[-1])
				files_count += self.recursive_copy_files(source_path=item, destination_path=path, override=override)
			else:
				file = os.path.join(destination_path, item.split('/')[-1])
				if not os.path.exists(file) or override:
					shutil.copyfile(item, file)
					files_count += 1
		return files_count

	def ensure_dir(self, file_path):
		if os.path.isfile(file_path):
			directory=os.path.dirname(file_path)
		else:
			directory=file_path
		if not os.path.isdir(directory):
			logging.info("Creating directory %s" % file_path)
			os.makedirs(directory)
		else:
			logging.warning("Directory %s already exists." % file_path)

	def get_licence_key(self):
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
				"PIANOTEQ_VERSION": [str(info['version'])],
				"PIANOTEQ_TRIAL": [str(info['trial'])]
			}
			errors=self.update_config(config)

		# Regenerate presets cache
		zynthian_engine_pianoteq(None, True)
