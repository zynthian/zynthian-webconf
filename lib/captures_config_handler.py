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
import uuid
import re
import fnmatch
import logging
import tornado.web
import json
import shutil
import requests
import jsonpickle
from collections import OrderedDict
from subprocess import check_output, call
from lib.zynthian_config_handler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# Soundfont Configuration
#------------------------------------------------------------------------------

class CapturesConfigHandler(tornado.web.RequestHandler):
	CAPTURES_DIRECTORY = "/zynthian/zynthian-my-data/capture"
	MOUNTED_CAPTURES_DIRECTORY = "/media/usb0"

	selectedTreeNode = 0
	selected_full_path = '';
	searchResult = '';
	maxTreeNodeIndex = 0

	def get_current_user(self):
		return self.get_secure_cookie("user")

	def prepare(self):
		self.genjson=False
		try:
			if self.get_query_argument("json"):
				self.genjson=True
		except:
			pass

	@tornado.web.authenticated
	def get(self, errors=None):
		config=OrderedDict([])
		self.maxTreeNodeIndex = 0
		captures = []
		try:
			if os.path.ismount(CapturesConfigHandler.MOUNTED_CAPTURES_DIRECTORY):
				captures.extend(self.walk_directory(CapturesConfigHandler.MOUNTED_CAPTURES_DIRECTORY,  'fa fa-fw fa-usb'))
			else:
				logging.info("/media/usb0 not found")
		except:
			pass

		try:
			captures.extend(self.walk_directory(CapturesConfigHandler.CAPTURES_DIRECTORY, 'fa fa-fw fa-file'))
		except:
			pass

		config['ZYNTHIAN_CAPTURES'] = json.dumps(captures)
		config['ZYNTHIAN_CAPTURES_SELECTION_NODE_ID'] = self.selectedTreeNode | 0

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="captures.html", config=config, title="Captures", errors=errors)

	def post(self):
		action = self.get_argument('ZYNTHIAN_CAPTURES_ACTION')
		self.selected_full_path =  self.get_argument('ZYNTHIAN_CAPTURES_FULLPATH')
		if action:
			errors = {
				'REMOVE': lambda: self.do_remove(),
				'RENAME': lambda: self.do_rename(),
				'DOWNLOAD': lambda: self.do_download()
			}[action]()

		if (action != 'DOWNLOAD'):
			self.get(errors)

	def do_remove(self):
		path = self.get_argument('ZYNTHIAN_CAPTURES_FULLPATH')
		try:
			if os.path.isdir(path):
				shutil.rmtree(path)
			else:
				os.remove(path)
		except:
			pass


	def do_rename(self):
		newName = ''

		if self.get_argument('ZYNTHIAN_CAPTURES_NAME'):
			newName = self.get_argument('ZYNTHIAN_CAPTURES_NAME')

		if newName:
			sourceFolder = self.get_argument('ZYNTHIAN_CAPTURES_FULLPATH')
			m = re.match('(.*/)(.*)', sourceFolder, re.M | re.I | re.S)
			if m:
				destinationFolder = m.group(1) + newName
				shutil.move(sourceFolder, destinationFolder)
				self.selected_full_path = destinationFolder;

	def do_download(self):
		if self.get_argument('ZYNTHIAN_CAPTURES_FULLPATH'):
			source_file = self.get_argument('ZYNTHIAN_CAPTURES_FULLPATH')
			filename = self.get_argument('ZYNTHIAN_CAPTURES_NAME')

			with open(source_file, 'rb') as f:
				try:
					while True:
						data = f.read(4096)
						if not data:
							break
						self.write(data)

					self.set_header('Content-Type', 'application/wav')
					self.set_header('Content-Disposition', 'attachment; filename=%s' % filename)
					self.finish()
				except Exception as exc:
					self.set_header('Content-Type', 'application/json')
					self.write(jsonpickle.encode({'data': format(exc)}))
			f.close()


	def walk_directory(self, directory, icon):
		captures = []
		fileList =  os.listdir(directory)
		fileList = sorted(fileList)
		for f in fnmatch.filter(fileList, '*.wav') + fnmatch.filter(fileList, '*.mid'):
			fullPath = os.path.join(directory, f)
			m = re.match('.*/(.*)', fullPath, re.M | re.I | re.S)
			text = ''

			if m:
				text = m.group(1)
			try:
				if self.selected_full_path == fullPath:
					self.selectedTreeNode = self.maxTreeNodeIndex # max is current right now
			except:
				pass
			capture = {
				'text': f,
				'name': text,
				'fullpath': fullPath,
				'icon': icon,
				'id': self.maxTreeNodeIndex}
			self.maxTreeNodeIndex+=1
			if os.path.isdir(os.path.join(directory, f)):
				capture['nodes'] = self.walk_directory(os.path.join(directory, f), icon)

			captures.append(capture)

		return captures
