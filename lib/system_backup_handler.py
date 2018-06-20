# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# System Backup Handler
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
import logging
import base64
import json
import shutil
import tornado.web
import zipfile
from io import BytesIO
from collections import OrderedDict
import time
import jsonpickle

from lib.zynthian_websocket_handler import ZynthianWebSocketMessageHandler, ZynthianWebSocketMessage

#------------------------------------------------------------------------------
# Module helper functions
#------------------------------------------------------------------------------

def get_backup_items(filename):
	with open(filename) as f:
		return f.read().splitlines()

#------------------------------------------------------------------------------
# Snapshot Config Handler
#------------------------------------------------------------------------------

class SystemBackupHandler(tornado.web.RequestHandler):

	SYSTEM_BACKUP_ITEMS_FILE = "/zynthian/config/system_backup_items.txt"
	DATA_BACKUP_ITEMS_FILE = "/zynthian/config/data_backup_items.txt"
	EXCLUDE_SUFFIX = ".exclude"


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
		self.do_get(None, errors)

	def do_get(self, active_tab, errors=None):
		config=OrderedDict([])

		config['ZYNTHIAN_SYSTEM_BACKUP_ITEMS'] = OrderedDict([])
		config['ZYNTHIAN_DATA_BACKUP_ITEMS'] = OrderedDict([])
		config['ZYNTHIAN_DATA_BACKUP_DIRECTORIES'] = []
		config['ZYNTHIAN_DATA_BACKUP_DIRECTORIES_EXCLUSIONS'] = []
		config['ZYNTHIAN_SYSTEM_BACKUP_DIRECTORIES'] = []
		config['ZYNTHIAN_SYSTEM_BACKUP_DIRECTORIES_EXCLUSIONS'] = []

		config['ZYNTHIAN_UPLOAD_MULTIPLE'] = False
		if active_tab:
			config['ZYNTHIAN_ACTIVE_TAB'] = active_tab
		else:
			config['ZYNTHIAN_ACTIVE_TAB'] = 'DATA_BACKUP'

		system_backup_items = get_backup_items(SystemBackupHandler.SYSTEM_BACKUP_ITEMS_FILE)
		for system_backup_folder in system_backup_items:
			if system_backup_folder.startswith("^"):
				config['ZYNTHIAN_SYSTEM_BACKUP_DIRECTORIES_EXCLUSIONS'].append(system_backup_folder[1:])
			else:
				config['ZYNTHIAN_SYSTEM_BACKUP_DIRECTORIES'].append(system_backup_folder)

		data_backup_items = get_backup_items(SystemBackupHandler.DATA_BACKUP_ITEMS_FILE)
		for data_backup_folder in data_backup_items:
			if data_backup_folder.startswith("^"):
				config['ZYNTHIAN_DATA_BACKUP_DIRECTORIES_EXCLUSIONS'].append(data_backup_folder[1:])
			else:
				config['ZYNTHIAN_DATA_BACKUP_DIRECTORIES'].append(data_backup_folder)

		def add_backup_item( dirname, subdirs, files, backup_directories_parameter ):
			if not dirname in config[backup_directories_parameter]:
				config[backup_directories_parameter][dirname]=[]
			for filename in files:
				config[backup_directories_parameter][dirname].append(filename)

		def add_data_backup_item( dirname, subdirs, files ):
			add_backup_item(dirname, subdirs, files, 'ZYNTHIAN_DATA_BACKUP_ITEMS')

		def add_system_backup_item( dirname, subdirs, files ):
			add_backup_item(dirname, subdirs, files, 'ZYNTHIAN_SYSTEM_BACKUP_ITEMS')

		self.walk_backup_items(add_system_backup_item, system_backup_items)
		self.walk_backup_items(add_data_backup_item, data_backup_items)

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="backup.html", config=config, title="Backup / Restore", errors=errors)


	@tornado.web.authenticated
	def post(self):
		action = self.get_argument('ZYNTHIAN_BACKUP_ACTION')
		if action:
			errors = {
				'SYSTEM_BACKUP': lambda: self.do_system_backup(),
				'DATA_BACKUP': lambda: self.do_data_backup(),
				'SAVE_SYSTEM_BACKUP_DIRECTORIES': lambda: self.do_save_backup_directories('ZYNTHIAN_SYSTEM_BACKUP_DIRECTORIES',
					'ZYNTHIAN_SYSTEM_BACKUP_DIRECTORIES_EXCLUSIONS',
					SystemBackupHandler.SYSTEM_BACKUP_ITEMS_FILE,
					'SYSTEM_BACKUP'),
				'SAVE_DATA_BACKUP_DIRECTORIES': lambda: self.do_save_backup_directories('ZYNTHIAN_DATA_BACKUP_DIRECTORIES',
					'ZYNTHIAN_DATA_BACKUP_DIRECTORIES_EXCLUSIONS',
					SystemBackupHandler.DATA_BACKUP_ITEMS_FILE,
					'DATA_BACKUP')
			}[action]()


	def do_save_backup_directories(self, backup_directory_parameter, backup_directory_exclusion_parameter, backup_file_name, tab_name):
		backup_directories = ''
		for backup_directory in self.get_argument(backup_directory_exclusion_parameter).split("\n"):
			if backup_directory:
				backup_directories+="^"
				backup_directories+=backup_directory
				backup_directories+='\n'

		backup_directories+=self.get_argument(backup_directory_parameter)

		with open(backup_file_name, 'w') as backup_file:
			backup_file.write(backup_directories)

		self.do_get(tab_name)


	def do_system_backup(self):
		self.do_backup('zynthian_system_backup',SystemBackupHandler.SYSTEM_BACKUP_ITEMS_FILE)


	def do_data_backup(self):
		self.do_backup('zynthian_data_backup', SystemBackupHandler.DATA_BACKUP_ITEMS_FILE)


	def do_backup(self, backupFileNamePrefix, backupItemsFileName):
		zipname='{0}{1}.zip'.format(backupFileNamePrefix, time.strftime("%Y%m%d-%H%M%S"))
		f=BytesIO()
		zf = zipfile.ZipFile(f, "w")
		def zip_backup_items(dirname, subdirs, files):
			logging.info(dirname)
			if dirname != '/':
				zf.write(dirname)
			for filename in files:
				logging.info(filename)
				zf.write(os.path.join(dirname, filename))
		backup_items = get_backup_items(backupItemsFileName)

		self.walk_backup_items(zip_backup_items, backup_items)

		zf.close()
		self.set_header('Content-Type', 'application/zip')
		self.set_header('Content-Disposition', 'attachment; filename=%s' % zipname)

		self.write(f.getvalue())
		f.close()
		self.finish()


	def walk_backup_items(self, worker, backup_items):
		excluded_folders = []
		for backupFolder in backup_items:
			sourceFolder = os.path.expandvars(backupFolder)
			if sourceFolder.startswith("^"):
				sourceFolder = os.path.expandvars(sourceFolder[1:])
				excluded_folders.append(sourceFolder)
				exclude_filename = '/' + os.path.basename(os.path.normpath(sourceFolder)) + SystemBackupHandler.EXCLUDE_SUFFIX
				with open(exclude_filename, "w") as exclude_file:
					for dirname, subdirs, files in os.walk(sourceFolder):
						for filename in files:
							exclude_file.write(os.path.join(dirname,filename) + '\n')
				logging.info(exclude_filename)
				worker('/', None , exclude_filename[1:].split(':')) #convert single string to array of 1 string
				os.remove(exclude_filename)
			else:
				try:
					for dirname, subdirs, files in os.walk(sourceFolder):
						if not any(dirname.startswith(s) for s in excluded_folders):
							worker(dirname, subdirs, files)

				except:
					pass


	def is_valid_restore_item(self, validRestoreItems, restoreMember):
		for validRestoreItem in validRestoreItems:
			if str("/" + restoreMember).startswith(os.path.expandvars(validRestoreItem)):
				return True
		return False


class RestoreMessageHandler(ZynthianWebSocketMessageHandler):

	@classmethod
	def is_registered_for(cls, handler_name):
		return handler_name == 'RestoreMessageHandler'


	def is_valid_restore_item(self, validRestoreItems, restoreMember):
		for validRestoreItem in validRestoreItems:
			if str("/" + restoreMember).startswith(os.path.expandvars(validRestoreItem)):
				return True
		return False


	def on_websocket_message(self, restoreFile):
		#fileinfo = self.request.files['ZYNTHIAN_RESTORE_FILE'][0]
		#restoreFile = fileinfo['filename']
		with open(restoreFile , "rb") as f:
			validRestoreItems = get_backup_items(SystemBackupHandler.SYSTEM_BACKUP_ITEMS_FILE)
			validRestoreItems += get_backup_items(SystemBackupHandler.DATA_BACKUP_ITEMS_FILE)

			with zipfile.ZipFile(f,'r') as restoreZip:
				for member in restoreZip.namelist():
					if self.is_valid_restore_item(validRestoreItems, member):
						logMessage = "restored: " + member
						restoreZip.extract(member, "/")
						logging.debug(logMessage)
						message = ZynthianWebSocketMessage('RestoreMessageHandler', logMessage)
						self.websocket.write_message(jsonpickle.encode(message))
					else:
						if member.endswith(SystemBackupHandler.EXCLUDE_SUFFIX):
							restoreZip.extract(member, "/")
							with open("/" + member, 'r') as exclude_file:
								message = ZynthianWebSocketMessage('RestoreMessageHandler',"<b>PLEASE ENSURE THAT THE FOLLOWING FILES EXIST:<br />" + exclude_file.read().replace('\n', '<br />') + "</b>")
								self.websocket.write_message(jsonpickle.encode(message))
							os.remove('/' + member)
						else:
							logging.warn("restore of " + member + " not permitted")

				restoreZip.close()
			f.close()
		os.remove(restoreFile)
		message = ZynthianWebSocketMessage('RestoreMessageHandler', 'EOCOMMAND')
		self.websocket.write_message(jsonpickle.encode(message))
