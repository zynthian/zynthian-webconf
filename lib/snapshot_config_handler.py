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


#------------------------------------------------------------------------------
# Snapshot Config Handler
#------------------------------------------------------------------------------

class SnapshotConfigHandler(tornado.web.RequestHandler):
	SNAPSHOTS_DIRECTORY = "/zynthian/zynthian-my-data/snapshots"
	LEADING_ZERO_BANK = 5
	LEADING_ZERO_PROGRAM = 3

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

		snapshots = self.walk_directory(SnapshotConfigHandler.SNAPSHOTS_DIRECTORY, 0, '', '')

		config['ZYNTHIAN_SNAPSHOTS'] = json.dumps(snapshots)
		config['ZYNTHIAN_SNAPSHOT_BANKS'] = self.get_existing_banks(snapshots, True)
		config['ZYNTHIAN_SNAPSHOT_NEXT_BANK_NUMBER'] = self.calculate_next_bank(self.get_existing_banks(snapshots, False))

		config['ZYNTHIAN_SNAPSHOT_PROGRAMS'] = map(lambda x: str(x).zfill(SnapshotConfigHandler.LEADING_ZERO_PROGRAM), list(range(1, 129)))
		try:
			selectedBank = 0
			#logging.info(int(self.get_argument('ZYNTHIAN_SNAPSHOT_SELECTION_BANK_NO')))
			#logging.info(int(self.get_argument('ZYNTHIAN_SNAPSHOT_SELECTION_PROGRAM')))
			for snapshot in snapshots:
				logging.info(snapshot)
				if int(snapshot['bank'])==int(self.get_argument('ZYNTHIAN_SNAPSHOT_SELECTION_BANK_NO')):
					if not selectedBank:
						selectedBank = snapshot['id']
					if snapshot['nodes']:
						for snapshot_program in snapshot['nodes']:
							try:
								if int(snapshot_program['program'])==int(self.get_argument('ZYNTHIAN_SNAPSHOT_SELECTION_PROGRAM')):
									selectedBank = snapshot_program['id']
							except:
								pass
			#logging.info("selectedBank: " + str(selectedBank))
			config['ZYNTHIAN_SNAPSHOT_SELECTION_NODE_ID']  = selectedBank
		except:
			config['ZYNTHIAN_SNAPSHOT_SELECTION_NODE_ID'] = 0

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="snapshots.html", config=config, title="Snapshots", errors=errors)


	def post(self):
		action = self.get_argument('ZYNTHIAN_SNAPSHOT_ACTION')
		if action:
			errors = {
        		'NEW_BANK': lambda: self.do_new_bank(),
        		'REMOVE': lambda: self.do_remove(),
				'SAVE': lambda: self.do_save()
    		}[action]()

		self.get(errors)

	def do_new_bank(self):
		newBank = self.get_argument('ZYNTHIAN_SNAPSHOT_NEXT_BANK_NUMBER')
		snapshots = self.walk_directory(SnapshotConfigHandler.SNAPSHOTS_DIRECTORY, 0, '', '')
		if newBank.zfill(SnapshotConfigHandler.LEADING_ZERO_BANK) in self.get_existing_banks(snapshots, False):
			return "Bank exists already"
		if newBank:
			bankDirectory = SnapshotConfigHandler.SNAPSHOTS_DIRECTORY + '/' + newBank.zfill(SnapshotConfigHandler.LEADING_ZERO_BANK) + '-Bank'+newBank
			if not os.path.exists(bankDirectory):
				os.makedirs(bankDirectory)

	def do_remove(self):
		fullPath = self.get_argument('ZYNTHIAN_SNAPSHOT_FULLPATH')
		if os.path.exists(fullPath):
			if os.path.isdir(fullPath):
				try:
					os.rmdir(fullPath)
				except OSError:
					return "Delete snapshots first!"
			else:
				os.remove(fullPath)

	def do_save(self):
		fullPath = self.get_argument('ZYNTHIAN_SNAPSHOT_FULLPATH')
		newFullPath = SnapshotConfigHandler.SNAPSHOTS_DIRECTORY + '/'
		if os.path.isdir(fullPath):
			newFullPath += self.get_argument('ZYNTHIAN_SNAPSHOT_SELECTION_BANK_NO')
			if self.get_argument('ZYNTHIAN_SNAPSHOT_NAME'):
				 newFullPath +=  '-' +  self.get_argument('ZYNTHIAN_SNAPSHOT_NAME')
			if os.path.exists(newFullPath):
				return "Bank exists already!"
		else:
			newFullPath += self.get_argument('ZYNTHIAN_SNAPSHOT_SELECTION_BANK') + '/' + self.get_argument('ZYNTHIAN_SNAPSHOT_SELECTION_PROGRAM')
			if (self.get_argument('ZYNTHIAN_SNAPSHOT_NAME')):
				newFullPath += '-' + self.get_argument('ZYNTHIAN_SNAPSHOT_NAME')
			newFullPath += '.zss'
			newBankDirectory = SnapshotConfigHandler.SNAPSHOTS_DIRECTORY + '/' + self.get_argument('ZYNTHIAN_SNAPSHOT_SELECTION_BANK')
			if os.path.exists(newFullPath):
				return "Snapshot exists already!"
			for existingSnapshot in os.listdir(newBankDirectory):
				existingFullPath =  newBankDirectory + '/' + existingSnapshot
				if fullPath!=existingFullPath and existingSnapshot.startswith(self.get_argument('ZYNTHIAN_SNAPSHOT_SELECTION_PROGRAM')):
					return "Bank and program exists already: " +  self.get_argument('ZYNTHIAN_SNAPSHOT_SELECTION_BANK') + '/' + existingSnapshot
		try:
			os.rename(fullPath, newFullPath)
		except OSError:
			return 'mv ' + fullPath + ' to ' + newFullPath + ' failed!'

	def get_existing_banks(self, snapshots, inclName):
		existingBanks = []

		for snapshot in snapshots:
			if snapshot['bank']:
				bankName = snapshot['bank'].zfill(SnapshotConfigHandler.LEADING_ZERO_BANK)
				if inclName and snapshot['bankName']:
					bankName += '-' + snapshot['bankName']
				existingBanks.append(bankName)
		#logging.info("existingbanks: " + str(existingBanks))
		return sorted(existingBanks)

	def calculate_next_bank(self, existingBanks):
		for i in range(1, 65536):
			if str(i).zfill(SnapshotConfigHandler.LEADING_ZERO_BANK) not in existingBanks:
				return i
		return ''

	def walk_directory(self, directory, idx, bankNumber, bankName):
		snapshots = []
		fileList =  os.listdir(directory)
		fileList = sorted(fileList)
		for f in fileList:
			fullPath = os.path.join(directory, f)
			m = re.match('.*/(\d*)-{0,1}(.*)', fullPath, re.M | re.I | re.S)
			bno = ''
			bname = ''
			text = ''
			progno = ''
			details = ''
			if m:
				#logging.info(m.group(0) + ";" + m.group(1) + ";" + m.group(2))
				if not bankNumber:
					bno =  m.group(1).zfill(SnapshotConfigHandler.LEADING_ZERO_BANK)
					bname = m.group(2)
					text = bname
				else:
					filename_parts = os.path.splitext(m.group(2))
					if len(filename_parts)>1 and filename_parts[1]:
						text = filename_parts[0]
					bno = bankNumber.zfill(SnapshotConfigHandler.LEADING_ZERO_BANK)
					bname = bankName
					progno = m.group(1).zfill(SnapshotConfigHandler.LEADING_ZERO_PROGRAM)
					with open(fullPath) as snapshotfile:
						logging.info(fullPath)
						try:
							details = json.load(snapshotfile)
						except:
							pass
						snapshotfile.close()
			snapshot = {
				'text': f,
				'name': text,
				'fullpath': fullPath,
				'id': idx,
				'bank': bno,
				'bankName': bname,
				'program': progno,
				'details': details}
			idx+=1
			if os.path.isdir(os.path.join(directory, f)):
				snapshot['nodes'] = self.walk_directory(os.path.join(directory, f), idx, bno, bname)
				idx+=len(snapshot['nodes'])
			snapshots.append(snapshot)
		return snapshots
