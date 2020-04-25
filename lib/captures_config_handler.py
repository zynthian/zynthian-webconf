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
import re
import fnmatch
import logging
import subprocess

import tornado.web
import json
import shutil
import jsonpickle
from collections import OrderedDict

#------------------------------------------------------------------------------
# Soundfont Configuration
#------------------------------------------------------------------------------

class CapturesConfigHandler(tornado.web.RequestHandler):
	CAPTURES_DIRECTORY = "/zynthian/zynthian-my-data/capture"
	MOUNTED_CAPTURES_DIRECTORY = "/media/usb0"

	selectedTreeNode = 0
	selected_full_path = ''
	searchResult = ''
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
		if self.get_argument('stream', None, True):
			self.do_download(self.get_argument('stream').replace("%27","'"))
		else:
			captures = []
			captures.append(self.create_node('wav'))
			captures.append(self.create_node('ogg'))
			captures.append(self.create_node('mid'))

			config['ZYNTHIAN_CAPTURES'] = json.dumps(captures)
			config['ZYNTHIAN_CAPTURES_SELECTION_NODE_ID'] = self.selectedTreeNode | 0

			if self.genjson:
				self.write(config)
			else:
				self.render("config.html", body="captures.html", config=config, title="Captures", errors=errors)

	def post(self):
		action = self.get_argument('ZYNTHIAN_CAPTURES_ACTION')
		self.selected_full_path =  self.get_argument('ZYNTHIAN_CAPTURES_FULLPATH').replace("%27","'")
		if action:
			errors = {
				'REMOVE': lambda: self.do_remove(),
				'RENAME': lambda: self.do_rename(),
				'DOWNLOAD': lambda: self.do_download(self.get_argument('ZYNTHIAN_CAPTURES_FULLPATH')),
				'CONVERT_OGG': lambda: self.do_convert_ogg()
			}[action]()

		if (action != 'DOWNLOAD'):
			self.get(errors)

	def do_remove(self):
		logging.info('removing {}'.format(self.selected_full_path))
		try:
			if os.path.isdir(self.selected_full_path):
				shutil.rmtree(self.selected_full_path)
			else:
				os.remove(self.selected_full_path)
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

	def do_download(self, fullpath):
		if fullpath:
			source_file = fullpath
			filename = os.path.split(fullpath)[1]

			with open(source_file, 'rb') as f:
				try:
					while True:
						data = f.read(4096)
						if not data:
							break
						self.write(data)

					self.set_header('Content-Type', self.get_content_type(filename))
					self.set_header('Content-Disposition', 'attachment; filename="%s"' % filename)
					self.finish()
				except Exception as exc:
					self.set_header('Content-Type', 'application/json')
					self.write(jsonpickle.encode({'data': format(exc)}))
			f.close()

	def do_convert_ogg(self):
		ogg_file_name = os.path.splitext(self.selected_full_path)[0]+'.ogg'
		cmd = 'oggenc "{}" -o "{}"'.format(self.selected_full_path, ogg_file_name)
		try:
			logging.info(cmd)
			subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
		except Exception as e:
			return e.output
		return

	def get_content_type(self, filename):
		m = re.match('(.*)\.(.*)', filename, re.M | re.I | re.S)
		if m:
			if m.group(2) == 'mid':
				return 'audio/midi'
			elif m.group(2) == 'ogg':
				return 'audio/ogg'
		return 'application/wav'

	def create_node(self, file_extension):
		captures = []
		root_capture = {
			'text': file_extension,
			'name': file_extension,
			'fullpath': 'ignore',
			'icon': '',
			'id': self.maxTreeNodeIndex
		}
		self.maxTreeNodeIndex += 1

		try:
			if os.path.ismount(CapturesConfigHandler.MOUNTED_CAPTURES_DIRECTORY):
				captures.extend(
					self.walk_directory(CapturesConfigHandler.MOUNTED_CAPTURES_DIRECTORY, 'fa fa-fw fa-usb', file_extension))
			else:
				logging.info("/media/usb0 not found")
		except:
			pass

		try:
			captures.extend(self.walk_directory(CapturesConfigHandler.CAPTURES_DIRECTORY, 'fa fa-fw fa-file', file_extension))
		except:
			pass
		root_capture['nodes'] = captures
		return root_capture

	def walk_directory(self, directory, icon, file_extension):
		captures = []
		fileList = os.listdir(directory)
		logging.info(directory)
		fileList = sorted(fileList)
		for f in fnmatch.filter(fileList, '*.%s' % file_extension):
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
				'text': f.replace("'","&#39;"),
				'name': text.replace("'","&#39;"),
				'fullpath': fullPath.replace("'","&#39;"),
				'icon': icon,
				'id': self.maxTreeNodeIndex}
			self.maxTreeNodeIndex+=1
			if os.path.isdir(os.path.join(directory, f)):
				capture['nodes'] = self.walk_directory(os.path.join(directory, f), icon)

			captures.append(capture)

		return captures
