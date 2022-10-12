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
import logging
import tornado.web
import zipfile
from io import BytesIO
from collections import OrderedDict
import time
import jsonpickle
from lib.zynthian_config_handler import ZynthianBasicHandler
from lib.zynthian_websocket_handler import ZynthianWebSocketMessageHandler, ZynthianWebSocketMessage

#------------------------------------------------------------------------------
# Module helper functions
#------------------------------------------------------------------------------

def get_backup_items(filename):
	try:
		with open(filename) as f:
			return f.read().splitlines()
	except:
		return []

#------------------------------------------------------------------------------
# Snapshot Config Handler
#------------------------------------------------------------------------------

class SystemBackupHandler(ZynthianBasicHandler):

	CONFIG_BACKUP_ITEMS_FILE = "/zynthian/config/config_backup_items.txt"
	DATA_BACKUP_ITEMS_FILE = "/zynthian/config/data_backup_items.txt"
	EXCLUDE_SUFFIX = ".exclude"


	@tornado.web.authenticated
	def get(self, errors=None):
		self.do_get("BACKUP/RESTORE", errors)


	def do_get(self, active_tab="BACKUP/RESTORE", errors=None):
		config=OrderedDict([])
		config['ACTIVE_TAB'] = active_tab
		config['ZYNTHIAN_UPLOAD_MULTIPLE'] = True

		config['CONFIG_BACKUP_ITEMS'] = OrderedDict([])
		config['CONFIG_BACKUP_DIRS'] = []
		config['CONFIG_BACKUP_DIRS_EXCLUDED'] = []

		config['DATA_BACKUP_ITEMS'] = OrderedDict([])
		config['DATA_BACKUP_DIRS'] = []
		config['DATA_BACKUP_DIRS_EXCLUDED'] = []

		config_backup_items = get_backup_items(SystemBackupHandler.CONFIG_BACKUP_ITEMS_FILE)
		for item in config_backup_items:
			if item.startswith("^"):
				config['CONFIG_BACKUP_DIRS_EXCLUDED'].append(item[1:])
			else:
				config['CONFIG_BACKUP_DIRS'].append(item)

		data_backup_items = get_backup_items(SystemBackupHandler.DATA_BACKUP_ITEMS_FILE)
		for item in data_backup_items:
			if item.startswith("^"):
				config['DATA_BACKUP_DIRS_EXCLUDED'].append(item[1:])
			else:
				config['DATA_BACKUP_DIRS'].append(item)

		def add_config_backup_item(dirname, subdirs, files):
			if not dirname in config['CONFIG_BACKUP_ITEMS']:
				config['CONFIG_BACKUP_ITEMS'][dirname]=[]
			for fname in files:
				config['CONFIG_BACKUP_ITEMS'][dirname].append(fname)

		def add_data_backup_item(dirname, subdirs, files):
			if not dirname in config['DATA_BACKUP_ITEMS']:
				config['DATA_BACKUP_ITEMS'][dirname]=[]
			for fname in files:
				config['DATA_BACKUP_ITEMS'][dirname].append(fname)

		self.walk_backup_items(add_config_backup_item, config_backup_items)
		self.walk_backup_items(add_data_backup_item, data_backup_items)

		super().get("backup.html", "Backup / Restore", config, errors)


	@tornado.web.authenticated
	def post(self):
		command = self.get_argument('_command', '')
		logging.info("COMMAND = {}".format(command))
		if command:
			errors = {
				#'RESTORE': pass,
				'BACKUP_ALL': lambda: self.do_backup_all(),
				'BACKUP_CONFIG': lambda: self.do_backup_config(),
				'BACKUP_DATA': lambda: self.do_backup_data(),
				'SAVE_BACKUP_CONFIG': lambda: self.do_save_backup_config()
			}[command]()


	def do_save_backup_config(self):
		# Save "Config" items
		backup_dirs = ''
		for dpath in self.get_argument('CONFIG_BACKUP_DIRS_EXCLUDED').split("\n"):
			if dpath:
				backup_dirs+="^{}\n".format(dpath)

		backup_dirs += self.get_argument('CONFIG_BACKUP_DIRS')

		with open(SystemBackupHandler.CONFIG_BACKUP_ITEMS_FILE, 'w') as backup_file:
			backup_file.write(backup_dirs)

		# Save "Data" items
		backup_dirs = ''
		for dpath in self.get_argument('DATA_BACKUP_DIRS_EXCLUDED').split("\n"):
			if dpath:
				backup_dirs+="^{}\n".format(dpath)

		backup_dirs += self.get_argument('DATA_BACKUP_DIRS')

		with open(SystemBackupHandler.DATA_BACKUP_ITEMS_FILE, 'w') as backup_file:
			backup_file.write(backup_dirs)

		# Reload active tab
		active_tab = self.get_argument("ACTIVE_TAB", "BACKUP/RESTORE")
		self.do_get(active_tab)


	def do_backup_all(self):
		backup_items = get_backup_items(SystemBackupHandler.CONFIG_BACKUP_ITEMS_FILE)
		backup_items += get_backup_items(SystemBackupHandler.DATA_BACKUP_ITEMS_FILE)
		self.do_backup('zynthian_backup', backup_items)


	def do_backup_config(self):
		backup_items = get_backup_items(SystemBackupHandler.CONFIG_BACKUP_ITEMS_FILE)
		self.do_backup('zynthian_config_backup', backup_items)


	def do_backup_data(self):
		backup_items = get_backup_items(SystemBackupHandler.DATA_BACKUP_ITEMS_FILE)
		self.do_backup('zynthian_data_backup', backup_items)


	def do_backup(self, fname_prefix, backup_items):
		zipname = '{0}{1}.zip'.format(fname_prefix, time.strftime("%Y%m%d-%H%M%S"))
		f=BytesIO()
		zf = zipfile.ZipFile(f, "w")

		def zip_backup_items(dirname, subdirs, files):
			logging.info(dirname)
			if dirname != '/':
				zf.write(dirname)
			for filename in files:
				logging.info(filename)
				zf.write(os.path.join(dirname, filename))

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
			validRestoreItems = get_backup_items(SystemBackupHandler.CONFIG_BACKUP_ITEMS_FILE)
			validRestoreItems += get_backup_items(SystemBackupHandler.DATA_BACKUP_ITEMS_FILE)

			with zipfile.ZipFile(f,'r') as restoreZip:
				for member in restoreZip.namelist():
					if self.is_valid_restore_item(validRestoreItems, member):
						logMessage = "Restored: " + member
						restoreZip.extract(member, "/")
						logging.debug(logMessage)
						message = ZynthianWebSocketMessage('RestoreMessageHandler', logMessage)
						self.websocket.write_message(jsonpickle.encode(message))
					else:
						if member.endswith(SystemBackupHandler.EXCLUDE_SUFFIX):
							restoreZip.extract(member, "/")
							with open("/" + member, 'r') as exclude_file:
								message = ZynthianWebSocketMessage('RestoreMessageHandler',"<b>Please ensure that the following files does exist:<br />" + exclude_file.read().replace('\n', '<br />') + "</b>")
								self.websocket.write_message(jsonpickle.encode(message))
							os.remove('/' + member)
						else:
							logging.warn("Restore of " + member + " not permitted")

				restoreZip.close()
			f.close()
		os.remove(restoreFile)
		SystemBackupHandler.update_sys()
		message = ZynthianWebSocketMessage('RestoreMessageHandler', 'EOCOMMAND')
		self.websocket.write_message(jsonpickle.encode(message))		
