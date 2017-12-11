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
import logging
import tornado.web
import json
import shutil
import requests
from collections import OrderedDict
from subprocess import check_output, call
from lib.ZynthianConfigHandler import ZynthianConfigHandler
from lib.musical_artifacts import MusicalArtifacts

#------------------------------------------------------------------------------
# Soundfont Configuration
#------------------------------------------------------------------------------

class PresetsConfigHandler(tornado.web.RequestHandler):
	PRESETS_DIRECTORY = "/zynthian/zynthian-my-data/presets"

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
		presets = self.walk_directory(PresetsConfigHandler.PRESETS_DIRECTORY, '', '')

		config['ZYNTHIAN_PRESETS'] = json.dumps(presets)

		config['ZYNTHIAN_PRESETS_SELECTION_NODE_ID'] = self.selectedTreeNode

		config['ZYNTHIAN_PRESETS_SEARCH_RESULT'] = self.searchResult

		config['ZYNTHIAN_PRESETS_MUSICAL_ARTIFACT_TAGS'] = self.get_argument('ZYNTHIAN_PRESETS_MUSICAL_ARTIFACT_TAGS','')

		config['ZYNTHIAN_UPLOAD_MULTIPLE'] = True

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="presets.html", config=config, title="Presets", errors=errors)

	def post(self):
		action = self.get_argument('ZYNTHIAN_PRESETS_ACTION')
		self.selected_full_path =  self.get_argument('ZYNTHIAN_PRESETS_FULLPATH')
		if action:
			errors = {
				'NEW': lambda: self.do_new_bank(),
				'REMOVE': lambda: self.do_remove(),
				'RENAME': lambda: self.do_rename(),
				'SEARCH': lambda: self.do_search(),
				'DOWNLOAD': lambda: self.do_download(),
				'REVISE_UPLOAD': lambda: self.do_revise_upload()
			}[action]()

		self.get(errors)

	def do_remove(self):
		path = self.get_argument('ZYNTHIAN_PRESETS_FULLPATH')
		try:
			if os.path.isdir(path):
				shutil.rmtree(path)
			else:
				os.remove(path)
		except:
			pass

	def do_new_bank(self):
		if 	self.get_argument('ZYNTHIAN_PRESETS_NEW_BANK_NAME'):
			newBank =  self.get_argument('ZYNTHIAN_PRESETS_FULLPATH') + "/" + self.get_argument('ZYNTHIAN_PRESETS_NEW_BANK_NAME')
			os.mkdir(newBank)
			self.selected_full_path = newBank

	def do_rename(self):
		newName = ''

		if 	self.get_argument('ZYNTHIAN_PRESETS_BANK_NAME'):
			newName = self.get_argument('ZYNTHIAN_PRESETS_BANK_NAME')
		if self.get_argument('ZYNTHIAN_PRESETS_PRESET_NAME'):
			newName = self.get_argument('ZYNTHIAN_PRESETS_PRESET_NAME')
			filename_parts = os.path.splitext(newName)
			if filename_parts[1] != "." + self.get_argument('ZYNTHIAN_PRESETS_BANK_TYPE'):
				newName += "." + self.get_argument('ZYNTHIAN_PRESETS_BANK_TYPE')
		if newName:
			sourceFolder = self.get_argument('ZYNTHIAN_PRESETS_FULLPATH')
			m = re.match('(.*/)(.*)', sourceFolder, re.M | re.I | re.S)
			if m:
				destinationFolder = m.group(1) + newName
				shutil.move(sourceFolder, destinationFolder)
				self.selected_full_path = destinationFolder;

	def do_search(self):
		try:
			self.searchResult = self.musical_artifacts.search_artifacts(self.get_argument('ZYNTHIAN_PRESETS_BANK_TYPE'), self.get_argument('ZYNTHIAN_PRESETS_MUSICAL_ARTIFACT_TAGS'))
		except OSError as err:
			logging.error(format(err))
			return format(err)


	def do_download(self):
		if self.get_argument('ZYNTHIAN_PRESETS_DOWNLOAD_FILE'):
			source_file = self.get_argument('ZYNTHIAN_PRESETS_DOWNLOAD_FILE')
			logging.debug("downloading: " + source_file)

			m = re.match('(.*/)(.*)', source_file, re.M | re.I | re.S)
			if m:
				destination_file = self.selected_full_path + "/" + m.group(2)
				file_type = self.get_argument('ZYNTHIAN_PRESETS_BANK_TYPE')
				downloaded_file = self.musical_artifacts.download_artifact(source_file, destination_file, file_type, self.selected_full_path)

				self.cleanup_download(self.selected_full_path, self.selected_full_path)

				self.selected_full_path = self.revise_filename(self.selected_full_path, downloaded_file, file_type)

	def do_revise_upload(self):
		try:
			new_upload_file = self.get_argument('ZYNTHIAN_UPLOAD_NEW_FILE','')
			if new_upload_file:
				filename_parts = os.path.splitext(new_upload_file)
				self.selected_full_path = self.revise_filename(os.path.dirname(new_upload_file), new_upload_file, filename_parts[1][1:])
		except OSError as err:
			logging.error(format(err))
			return format(err)


	def get_preset_number_padding(self, file_type):
		# in case we need to differentiate between 4 and 5
		return 4

	def revise_filename(self, selected_full_path, downloaded_file, file_type):
		m = re.match('.*/(\d*)-{0,1}(.*)', downloaded_file, re.M | re.I | re.S)
		if m:
			filename =  m.group(2)

			file_list =  os.listdir(selected_full_path)
			file_list = sorted(file_list)

			existing_program_numbers = []
			for f in file_list:
				if downloaded_file != selected_full_path + "/" + f:
					# logging.info(f)
					fp = os.path.join(selected_full_path, f)
					m3 = re.match('.*/(\d*)-{0,1}(.*)', fp, re.M | re.I | re.S)
					if m3:
						try:
							existing_program_numbers.append(int(m3.group(1)))
						except:
							pass
			# logging.info(existing_program_numbers)

			if  m.group(1) and not int(m.group(1)) in existing_program_numbers:
				current_index = int(m.group(1))
			else:
				current_index = 0
				for existing_program_number in existing_program_numbers:
					if existing_program_number != current_index:
						current_index +=1
						break
					current_index +=1

			shutil.move(downloaded_file,selected_full_path + "/" + str(current_index).zfill(self.get_preset_number_padding(file_type)) + "-" + filename)


	def cleanup_download(self, currentDirectory, targetDirectory):
		fileList =  os.listdir(currentDirectory)
		for f in fileList:
			sourcePath = os.path.join(currentDirectory, f)

			if os.path.isdir(sourcePath):
				self.cleanup_download(sourcePath, targetDirectory)
				shutil.rmtree(sourcePath)
			else:
				if not f.startswith(".") and  f.endswith("." + self.get_argument('ZYNTHIAN_PRESETS_BANK_TYPE')):
					targetPath = os.path.join(targetDirectory, f)
					shutil.move(sourcePath, targetPath)


	def walk_directory(self, directory, nodeType, bankType):
		banks = []
		fileList =  os.listdir(directory)
		fileList = sorted(fileList)
		for f in fileList:
			fullPath = os.path.join(directory, f)
			m = re.match('.*/(.*)', fullPath, re.M | re.I | re.S)
			text = ''
			nextNodeType = ''
			if m:
				if nodeType:
					if nodeType == 'BANK_TYPE':
						nextNodeType = 'BANK'
						text =  m.group(1)
					else:
						nextNodeType = 'PRESET'
						text = m.group(1)
				else:
					bankType = m.group(1)
					nextNodeType = 'BANK_TYPE'
					text = m.group(1)

			try:
				if self.selected_full_path == fullPath:
					self.selectedTreeNode = self.maxTreeNodeIndex
			except:
				pass
			bank = {
				'text': f,
				'name': text,
				'fullpath': fullPath,
				'id': self.maxTreeNodeIndex,
				'bankType': bankType,
				'nodeType': nextNodeType}
			self.maxTreeNodeIndex+=1
			if os.path.isdir(os.path.join(directory, f)):
				bank['nodes'] = self.walk_directory(os.path.join(directory, f), nextNodeType, bankType)

			banks.append(bank)

		return banks
