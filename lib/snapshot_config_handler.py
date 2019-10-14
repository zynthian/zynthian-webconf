# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Snapshot Manager Handler
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
from collections import OrderedDict

from lib.zynthian_config_handler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# Snapshot Config Handler
#------------------------------------------------------------------------------

class SnapshotConfigHandler(ZynthianConfigHandler):

	my_data_dir = os.environ.get('ZYNTHIAN_MY_DATA_DIR',"/zynthian/zynthian-my-data")

	SNAPSHOTS_DIRECTORY = my_data_dir + "/snapshots"
	BANK_LEADING_ZEROS = 5
	PROG_LEADING_ZEROS = 3


	@tornado.web.authenticated
	def get(self, errors=None):
		config=OrderedDict([])

		snapshots = self.get_snapshots_data()
		#logging.debug(snapshot)

		config['SNAPSHOTS'] = json.dumps(snapshots)
		config['BANKS'] = self.get_existing_banks(snapshots, True)
		config['NEXT_BANK_NUM'] = self.calculate_next_bank(self.get_existing_banks(snapshots, False))
		config['PROGS_NUM'] = map(lambda x: str(x).zfill(SnapshotConfigHandler.PROG_LEADING_ZEROS), list(range(1, 129)))

		# Try to maintain selection after a POST action...
		selected_node = 0
		try:
			for ssbank in snapshots:
				try:
					if int(ssbank['bank_num'])==int(self.get_argument('SEL_BANK_NUM')):
						if not selected_node:
							selected_node = ssbank['id']

					if ssbank['nodes']:
						for ssprog in ssbank['nodes']:
							try:
								if int(ssprog['prog_num'])==int(self.get_argument('SEL_PROG_NUM')):
									selected_node = ssprog['id']
							except:
								pass
				except:
					pass

		except Exception as e:
			logging.debug("ERROR:" + str(e))

		config['SEL_NODE_ID'] = selected_node
		logging.info("Selected Node: {}".format(selected_node))

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="snapshots.html", config=config, title="Snapshots", errors=errors)


	@tornado.web.authenticated
	def post(self):
		action = self.get_argument('ACTION')
		if action:
			errors = {
        		'NEW_BANK': lambda: self.do_new_bank(),
        		'REMOVE': lambda: self.do_remove(),
				'SAVE': lambda: self.do_save()
    		}[action]()

		self.get(errors)


	def do_new_bank(self):
		new_bank_num = self.get_argument('NEW_BANK_NUM')
		snapshots = self.get_snapshots_data()
		if new_bank_num.zfill(SnapshotConfigHandler.BANK_LEADING_ZEROS) in self.get_existing_banks(snapshots, False):
			return "Bank already exists!"
		if new_bank_num:
			bank_dpath = SnapshotConfigHandler.SNAPSHOTS_DIRECTORY + '/' + new_bank_num.zfill(SnapshotConfigHandler.BANK_LEADING_ZEROS) + '-Bank' + new_bank_num
			if not os.path.exists(bank_dpath):
				os.makedirs(bank_dpath)


	def do_remove(self):
		fullPath = self.get_argument('SEL_FULLPATH')
		if os.path.exists(fullPath):
			if os.path.isdir(fullPath):
				try:
					os.rmdir(fullPath)
				except OSError:
					return "Can't delete a bank with snapshots. Delete snapshots first!"
			else:
				os.remove(fullPath)


	def do_save(self):
		fullPath = self.get_argument('SEL_FULLPATH')
		newFullPath = SnapshotConfigHandler.SNAPSHOTS_DIRECTORY + '/'
		
		# Save Bank
		if os.path.isdir(fullPath):
			newFullPath += self.get_argument('SEL_BANK_NUM')
			if self.get_argument('SEL_NAME'):
				 newFullPath +=  '-' +  self.get_argument('SEL_NAME')
			if os.path.exists(newFullPath):
				return "Bank exists already!"
		# Save Program
		else:
			try:
				newFullPath += self.get_argument('SEL_BANK') + '/'
				if not os.path.exists(newFullPath):
					return "Bank doesn't exist"
			except:
				pass

			preset_fname=None
			try:
				preset_fname =  self.get_argument('SEL_PROG_NUM')
				if self.get_argument('SEL_NAME'):
					preset_fname += '-' + self.get_argument('SEL_NAME')
			except:
				if self.get_argument('SEL_NAME'):
					preset_fname =  self.get_argument('SEL_NAME')
			
			if not preset_fname:
				return "You should specify some destination."

			newFullPath += preset_fname + '.zss'
			if newFullPath!=fullPath and os.path.exists(newFullPath):
				return "This bank/program slot is already used: " +  newFullPath

		try:
			os.rename(fullPath, newFullPath)
		except OSError:
			return 'Move ' + fullPath + ' to ' + newFullPath + ' failed!'


	def get_existing_banks(self, snapshots, incl_name):
		existing_banks = []

		for snapshot in snapshots:
			if not snapshot['prog_num'] and snapshot['bank_num']:
				bank_name = snapshot['bank_num'].zfill(SnapshotConfigHandler.BANK_LEADING_ZEROS)
				if incl_name and snapshot['bank_name']:
					bank_name += '-' + snapshot['bank_name']
				existing_banks.append(bank_name)

		#logging.info("existingbanks: " + str(existing_banks))
		return sorted(existing_banks)


	def calculate_next_bank(self, existing_banks):
		for i in range(1, 65536):
			if str(i).zfill(SnapshotConfigHandler.BANK_LEADING_ZEROS) not in existing_banks:
				return i
		return ''


	def get_snapshots_data(self):
		return self.walk_directory(SnapshotConfigHandler.SNAPSHOTS_DIRECTORY)


	def walk_directory(self, directory, idx=0, _bank_num=None, _bank_name=None):
		snapshots = []
		file_list =  sorted(os.listdir(directory))
		for f in file_list:
			fullpath = os.path.join(directory, f)
			if os.path.isdir(fullpath):
				parts = f.split("-", 1)
				bank_num = parts[0]
				if len(parts)==2:
					bank_name = parts[1]
				else:
					bank_name = ""
				prog_name = ""
				prog_num = ""
				prog_details = ""
				name = bank_name
			else:
				parts = f.split(".", 1)
				if len(parts)==2:
					fname = parts[0]
					fext =parts[1]
					if fext=="zss":
						if _bank_num is not None:
							bank_num = _bank_num.zfill(SnapshotConfigHandler.BANK_LEADING_ZEROS)
							bank_name = _bank_name
							parts = fname.split("-")
							prog_num = parts[0]
							if len(parts)==2:
								prog_name = parts[1]
							else:
								prog_name = ""
						else:
							bank_num = ''
							bank_name = ''
							prog_num = ''
							prog_name = fname
						name = prog_name

						with open(fullpath) as ssfile:
							try:
								prog_details = json.load(ssfile)
							except:
								pass
							ssfile.close()

			snapshot = {
				'id': idx,
				'text': f,
				'name': name,
				'fullpath': fullpath,
				'bank_num': bank_num,
				'bank_name': bank_name,
				'prog_num': prog_num,
				'prog_name': prog_name,
				'prog_details': prog_details
			}
			
			idx += 1
			if os.path.isdir(fullpath):
				snapshot['nodes'] = self.walk_directory(fullpath, idx, bank_num, bank_name)
				idx+=len(snapshot['nodes'])

			snapshots.append(snapshot)

		return snapshots
