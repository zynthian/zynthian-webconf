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
import json
import base64
import shutil
import base64
import logging
import tornado.web
from collections import OrderedDict

from lib.zynthian_config_handler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# Snapshot Config Handler
#------------------------------------------------------------------------------


class SnapshotConfigHandler(ZynthianConfigHandler):

	my_data_dir = os.environ.get('ZYNTHIAN_MY_DATA_DIR',"/zynthian/zynthian-my-data")

	SNAPSHOTS_DIRECTORY = my_data_dir + "/snapshots"
	PROFILES_DIRECTORY = "%s/midi-profiles" % os.environ.get("ZYNTHIAN_CONFIG_DIR")

	@tornado.web.authenticated
	def get(self, errors=None):
		config=OrderedDict([])

		ssdata = self.get_snapshots_data()
		#logging.debug(snapshot)

		config['SNAPSHOTS'] = json.dumps(ssdata)
		config['BANKS'] = self.get_existing_banks(ssdata, True)
		config['NEXT_BANK_NUM'] = self.calculate_next_bank(self.get_existing_banks(ssdata, False))
		config['PROGS_NUM'] = map(lambda x: str(x).zfill(3), list(range(0, 128)))
		config['MIDI_PROFILE_SCRIPTS'] = {os.path.splitext(x)[0]:  "%s/%s" % (self.PROFILES_DIRECTORY, x) for x in os.listdir(self.PROFILES_DIRECTORY)}

		# Try to maintain selection after a POST action...
		selected_node = 0
		try:
			for ssbank in ssdata:
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
					action = self.get_argument('ACTION', '')
					if action == 'SAVE_AS_DEFAULT' and ssbank['name'] == 'default':
						selected_node = ssbank['id']
					elif action == 'SAVE_AS_LAST_STATE' and ssbank['name'] == 'last_state':
						selected_node = ssbank['id']

		except Exception as e:
			logging.debug("ERROR:" + str(e))

		config['SEL_NODE_ID'] = selected_node
		logging.debug("Selected Node: {}".format(selected_node))

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
				'SAVE': lambda: self.do_save(),
				'SAVE_AS_DEFAULT': lambda: self.do_save_as_default(),
				'SAVE_AS_LAST_STATE': lambda: self.do_save_as_last_state()
			}[action]()

		self.get(errors)


	def do_new_bank(self):
		existing_banks = self.get_existing_banks(self.get_snapshots_data(), False)
		new_bank_dname = self.get_argument('NEW_BANK_NUM', str(self.calculate_next_bank(existing_banks))).zfill(3)
		if new_bank_dname in existing_banks:
			return "Bank already exists!"
		if new_bank_dname:
			bank_dpath = self.SNAPSHOTS_DIRECTORY + '/' + new_bank_dname
			if not os.path.exists(bank_dpath):
				os.makedirs(bank_dpath)


	def do_remove(self):
		fullPath = self.get_argument('SEL_FULLPATH')
		if os.path.exists(fullPath):
			if os.path.isdir(fullPath):
				shutil.rmtree(fullPath)
			else:
				os.remove(fullPath)


	def do_save(self):
		fullPath = self.get_argument('SEL_FULLPATH')
		newFullPath = SnapshotConfigHandler.SNAPSHOTS_DIRECTORY + '/'
		
		# Save Bank
		if os.path.isdir(fullPath):
			newFullPath += self.get_argument('SEL_BANK_NUM')
			if self.get_argument('SEL_NAME'):
				newFullPath += '-' + self.get_argument('SEL_NAME')
			if os.path.exists(newFullPath):
				return "Bank exists already!"
		# Save Program
		else:
			try:
				newFullPath += self.get_argument('SEL_BANK') + '/'
				if not os.path.exists(newFullPath):
					return "Bank doesn't exist. You must create it before moving snapshots inside it."
			except:
				pass

			sshot_fname=None
			try:
				sshot_fname =  self.get_argument('SEL_PROG_NUM')
				if self.get_argument('SEL_NAME'):
					sshot_fname += '-' + self.get_argument('SEL_NAME')
			except:
				if self.get_argument('SEL_NAME'):
					sshot_fname =  self.get_argument('SEL_NAME')
			
			if not sshot_fname:
				return "You must specify a name or program number for the snapshot."

			newFullPath += sshot_fname + '.zss'
			if newFullPath!=fullPath and os.path.exists(newFullPath):
				return "This bank/program combination is already used: " +  newFullPath

		try:
			os.rename(fullPath, newFullPath)
		except OSError:
			return 'Move ' + fullPath + ' to ' + newFullPath + ' failed!'


	def do_save_as_default(self):
		dest = self.SNAPSHOTS_DIRECTORY + "/default.zss"
		src = self.get_argument('SEL_FULLPATH')
		logging.info("Copy %s to %s" % (src, dest))
		shutil.copyfile(src, dest)


	def do_save_as_last_state(self):
		dest = self.SNAPSHOTS_DIRECTORY + "/last_state.zss"
		src = self.get_argument('SEL_FULLPATH')
		logging.info("Copy %s to %s" % (src, dest))
		shutil.copyfile(src, dest)


	def get_existing_banks(self, snapshot_data, incl_name):
		existing_banks = []

		for item in snapshot_data:
			if item['node_type']=='BANK':
				bank_dname = item['bank_num'].zfill(3)
				if incl_name and item['bank_name']:
					bank_dname += '-' + item['bank_name']
				existing_banks.append(bank_dname)

		#logging.info("existingbanks: " + str(existing_banks))
		return sorted(existing_banks)


	def calculate_next_bank(self, existing_banks):
		for i in range(0, 128):
			if str(i).zfill(3) not in existing_banks:
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
				node_type = "BANK"
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
				fname = f[:-4]
				fext = f[-4:]
				if fext==".zss":
					node_type = "SNAPSHOT"
					if _bank_num is not None:
						bank_num = _bank_num.zfill(3)
						bank_name = _bank_name
						parts = fname.split("-", 1)
						prog_num = parts[0]
						if len(parts)==2:
							prog_name = fname[len(prog_num)+1:]
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
				else:
					continue

			snapshot = {
				'id': idx,
				'text': f,
				'name': name,
				'fullpath': fullpath,
				'node_type': node_type,
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

class SnapshotRemoveOptionHandler(tornado.web.RequestHandler):

	def get_current_user(self):
		return self.get_secure_cookie("user")

	@tornado.web.authenticated
	def post(self, snapshot_file, remove_option_key):
		result = {}

		try:
			logging.info("Removing option {} in {}".format(remove_option_key, snapshot_file))
			data = []
			with open(snapshot_file, "r") as fp:
				data = json.load(fp)
				del data['midi_profile_state'][remove_option_key]

			with open(snapshot_file, "w") as fp:
				json.dump(data, fp)

			result = data


		except Exception as err:
			result['errors'] = str(err)
			logging.error(err)

		# JSON Ouput
		if result:
			self.write(result)

class SnapshotAddOptionsHandler(tornado.web.RequestHandler):
	PROFILES_DIRECTORY = "%s/midi-profiles" % os.environ.get("ZYNTHIAN_CONFIG_DIR")

	def get_current_user(self):
		return self.get_secure_cookie("user")

	@tornado.web.authenticated
	def post(self, snapshot_file_b64, midi_profile_script_b64):
		result = {}

		try:
			snapshot_file = str(base64.b64decode(snapshot_file_b64), 'utf-8')
			midi_profile_script = str(base64.b64decode(midi_profile_script_b64), 'utf-8')
			logging.info("Add option values of {} into {}".format(midi_profile_script, snapshot_file))
			data = []
			with open(snapshot_file, "r") as fp:
				data = json.load(fp)

			p = re.compile("export ZYNTHIAN_MIDI_(\w*)=\"(.*)\"")
			profile_values = {}
			with open(midi_profile_script, "r") as midi_fp:
				for line in midi_fp:
					if line[0] == '#':
						continue
					m = p.match(line)
					if m:
						profile_values[m.group(1)] = m.group(2)

			for profile_value in profile_values:
				data['midi_profile_state'][profile_value] = profile_values[profile_value]

			with open(snapshot_file, "w") as fp:
				json.dump(data, fp)

			result = data

		except Exception as err:
			result['errors'] = str(err)
			logging.error(err)

		# JSON Ouput
		if result:
			self.write(result)
