# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# SoundFont Manager Handler
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
import logging
import tornado.web
import json
import shutil
import requests
from collections import OrderedDict
from subprocess import check_output, call

from lib.zynthian_config_handler import ZynthianConfigHandler
from lib.musical_artifacts import MusicalArtifacts

#------------------------------------------------------------------------------
# Soundfont Configuration
#------------------------------------------------------------------------------



class SoundfontConfigHandler(tornado.web.RequestHandler):
	
	SOUNDFONTS_DIRECTORY = "/zynthian/zynthian-my-data/soundfonts"

	selectedTreeNode = 0
	selected_full_path = '';
	searchResult = '';
	maxTreeNodeIndex = 0
	musical_artifacts = MusicalArtifacts()


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
		soundfonts = self.walk_directory(SoundfontConfigHandler.SOUNDFONTS_DIRECTORY, '', '')

		config['ZYNTHIAN_SOUNDFONTS'] = json.dumps(soundfonts)

		config['ZYNTHIAN_SOUNDFONT_SELECTION_NODE_ID'] = self.selectedTreeNode

		config['ZYNTHIAN_SOUNDFONT_SEARCH_RESULT'] = self.searchResult

		config['ZYNTHIAN_SOUNDFONT_MUSICAL_ARTIFACT_TAGS'] = self.get_argument('ZYNTHIAN_SOUNDFONT_MUSICAL_ARTIFACT_TAGS','')

		config['ZYNTHIAN_UPLOAD_MULTIPLE'] = True

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="soundfonts.html", config=config, title="Soundfonts", errors=errors)


	@tornado.web.authenticated
	def post(self):
		action = self.get_argument('ZYNTHIAN_SOUNDFONT_ACTION')
		self.selected_full_path =  self.get_argument('ZYNTHIAN_SOUNDFONT_FULLPATH')
		if action:
			errors = {
				'NEW': lambda: self.do_new_bank(),
				'REMOVE': lambda: self.do_remove(),
				'RENAME': lambda: self.do_rename(),
				'SEARCH': lambda: self.do_search(),
				'DOWNLOAD': lambda: self.do_download()
			}[action]()

		self.get(errors)


	def do_remove(self):
		path = self.get_argument('ZYNTHIAN_SOUNDFONT_FULLPATH')
		try:
			if os.path.isdir(path):
				shutil.rmtree(path)
			else:
				os.remove(path)
		except:
			pass


	def do_new_bank(self):
		if 	self.get_argument('ZYNTHIAN_SOUNDFONT_NEW_BANK_NAME'):
			newBank =  self.get_argument('ZYNTHIAN_SOUNDFONT_FULLPATH') + "/" + self.get_argument('ZYNTHIAN_SOUNDFONT_NEW_BANK_NAME')
			os.mkdir(newBank)
			self.selected_full_path = newBank


	def do_rename(self):
		newName = ''

		if 	self.get_argument('ZYNTHIAN_SOUNDFONT_BANK_NAME'):
			newName = self.get_argument('ZYNTHIAN_SOUNDFONT_BANK_NAME')
		if self.get_argument('ZYNTHIAN_SOUNDFONT_NAME'):
			newName = self.get_argument('ZYNTHIAN_SOUNDFONT_NAME')
			filename_parts = os.path.splitext(newName)
			if filename_parts[1] != "." + self.get_argument('ZYNTHIAN_SOUNDFONT_SOUNDFONT_TYPE'):
				newName += "." + self.get_argument('ZYNTHIAN_SOUNDFONT_SOUNDFONT_TYPE')
		if newName:
			sourceFolder = self.get_argument('ZYNTHIAN_SOUNDFONT_FULLPATH')
			m = re.match('(.*/)(.*)', sourceFolder, re.M | re.I | re.S)
			if m:
				destinationFolder = m.group(1) + newName
				shutil.move(sourceFolder, destinationFolder)
				self.selected_full_path = destinationFolder;


	def do_search(self):
		try:
			self.searchResult = self.musical_artifacts.search_artifacts(self.get_argument('ZYNTHIAN_SOUNDFONT_SOUNDFONT_TYPE'), self.get_argument('ZYNTHIAN_SOUNDFONT_MUSICAL_ARTIFACT_TAGS'))
		except OSError as err:
			logging.error(format(err))
			return format(err)


	def do_download(self):
		if self.get_argument('ZYNTHIAN_SOUNDFONT_DOWNLOAD_FILE'):
			sourceFile = self.get_argument('ZYNTHIAN_SOUNDFONT_DOWNLOAD_FILE')
			logging.debug("downloading: " + sourceFile)

			m = re.match('(.*/)(.*)', sourceFile, re.M | re.I | re.S)
			if m:
				destinationFile = self.selected_full_path + "/" + m.group(2)
				downloadedFile = self.musical_artifacts.download_artifact(sourceFile, destinationFile, self.get_argument('ZYNTHIAN_SOUNDFONT_SOUNDFONT_TYPE'), self.selected_full_path)
				self.cleanup_download(self.selected_full_path, self.selected_full_path)
				self.selected_full_path = downloadedFile


	def cleanup_download(self, currentDirectory, targetDirectory):
		fileList =  os.listdir(currentDirectory)
		for f in fileList:
			sourcePath = os.path.join(currentDirectory, f)
			if os.path.isdir(sourcePath):
				self.cleanup_download(sourcePath, targetDirectory)
				shutil.rmtree(sourcePath)
			else:
				if not f.startswith(".") and  f.endswith("." + self.get_argument('ZYNTHIAN_SOUNDFONT_SOUNDFONT_TYPE')):
					targetPath = os.path.join(targetDirectory, f)
					shutil.move(sourcePath, targetPath)


	def walk_directory(self, directory, nodeType, soundfontType):
		soundfonts = []
		fileList =  os.listdir(directory)
		fileList = sorted(fileList)
		for f in fileList:
			fullPath = os.path.join(directory, f)
			m = re.match('.*/(.*)', fullPath, re.M | re.I | re.S)
			text = ''
			nextNodeType = ''
			if m:
				if nodeType:
					if nodeType == 'SOUNDFONT_TYPE':
						if os.path.splitext(m.group(1))[1]==".sf2":
							nextNodeType = 'SOUNDFONT'
						else:
							nextNodeType = 'BANK'
						text =  m.group(1)
					else:
						nextNodeType = 'SOUNDFONT'
						text = m.group(1)
				else:
					soundfontType = m.group(1)
					if m.group(1) == "sf2":
						nextNodeType = 'BANK'
					else:
						nextNodeType = 'SOUNDFONT_TYPE'
					text = m.group(1)

			try:
				if self.selected_full_path == fullPath:
					self.selectedTreeNode = self.maxTreeNodeIndex
			except:
				pass
			soundfont = {
				'text': f,
				'name': text,
				'fullpath': fullPath,
				'id': self.maxTreeNodeIndex,
				'soundfontType': soundfontType,
				'nodeType': nextNodeType}
			self.maxTreeNodeIndex+=1
			if os.path.isdir(os.path.join(directory, f)):
				soundfont['nodes'] = self.walk_directory(os.path.join(directory, f), nextNodeType, soundfontType)

			soundfonts.append(soundfont)
		#logging.info(soundfonts)
		return soundfonts
