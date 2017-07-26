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
	SNAPSHOT_DIRECTORY = "/zynthian/zynthian-my-data/snapshots"
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

		snapshots = self.walkDirectory(SnapshotConfigHandler.SNAPSHOT_DIRECTORY, 0, '', '')

		config['ZYNTHIAN_SNAPSHOTS'] = json.dumps(snapshots)
		config['ZYNTHIAN_SNAPSHOT_BANKS'] = self.getExistingBanks(snapshots, True)
		config['ZYNTHIAN_SNAPSHOT_NEXT_BANK_NUMBER'] = self.calculateNextBank(self.getExistingBanks(snapshots, False))

		config['ZYNTHIAN_SNAPSHOT_PROGRAMS'] = map(lambda x: str(x).zfill(SnapshotConfigHandler.LEADING_ZERO_PROGRAM), list(range(1, 129)))
		try:
			selectedBank = 0
			logging.info(int(self.get_argument('ZYNTHIAN_SNAPSHOT_SELECTION_BANK_NO')))
			logging.info(int(self.get_argument('ZYNTHIAN_SNAPSHOT_SELECTION_PROGRAM')))
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
			logging.info(selectedBank)
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
        		'NEW_BANK': lambda: self.doNewBank(),
        		'REMOVE': lambda: self.doRemove(),
				'SAVE': lambda: self.doSave()
    		}[action]()

		self.get(errors)

	def doNewBank(self):
		newBank = self.get_argument('ZYNTHIAN_SNAPSHOT_NEXT_BANK_NUMBER')
		snapshots = self.walkDirectory(SnapshotConfigHandler.SNAPSHOT_DIRECTORY, 0, '', '')
		if newBank.zfill(SnapshotConfigHandler.LEADING_ZERO_BANK) in self.getExistingBanks(snapshots, False):
			return "Bank exists already"
		if newBank:
			bankDirectory = SnapshotConfigHandler.SNAPSHOT_DIRECTORY + '/' + newBank.zfill(SnapshotConfigHandler.LEADING_ZERO_BANK) + '-Bank'+newBank
			if not os.path.exists(bankDirectory):
				os.makedirs(bankDirectory)

	def doRemove(self):
		fullPath = self.get_argument('ZYNTHIAN_SNAPSHOT_FULLPATH')
		if os.path.exists(fullPath):
			if os.path.isdir(fullPath):
				try:
					os.rmdir(fullPath)
				except OSError:
					return "Delete snapshots first!"
			else:
				os.remove(fullPath)

	def doSave(self):
		fullPath = self.get_argument('ZYNTHIAN_SNAPSHOT_FULLPATH')
		newFullPath = SnapshotConfigHandler.SNAPSHOT_DIRECTORY + '/'
		if os.path.isdir(fullPath):
			newFullPath += self.get_argument('ZYNTHIAN_SNAPSHOT_SELECTION_BANK_NO') + '-' +  self.get_argument('ZYNTHIAN_SNAPSHOT_NAME')
			if os.path.exists(newFullPath):
				return "Bank exists already!"
		else:
			newFullPath += self.get_argument('ZYNTHIAN_SNAPSHOT_SELECTION_BANK') + '/' + self.get_argument('ZYNTHIAN_SNAPSHOT_SELECTION_PROGRAM') + '-' + self.get_argument('ZYNTHIAN_SNAPSHOT_NAME') + '.zss'
			newBankDirectory = SnapshotConfigHandler.SNAPSHOT_DIRECTORY + '/' + self.get_argument('ZYNTHIAN_SNAPSHOT_SELECTION_BANK')
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

	def getExistingBanks(self, snapshots, inclName):
		existingBanks = []

		for snapshot in snapshots:
			if snapshot['bank']:
				bankName = snapshot['bank'].zfill(SnapshotConfigHandler.LEADING_ZERO_BANK)
				if inclName:
					bankName += '-' + snapshot['bankName']
				existingBanks.append(bankName)
		return sorted(existingBanks)

	def calculateNextBank(self, existingBanks):
		for i in range(1, 65536):
			if str(i).zfill(SnapshotConfigHandler.LEADING_ZERO_BANK) not in existingBanks:
				return i
		return ''

	def walkDirectory(self, directory, idx, bankNumber, bankName):
		snapshots = []
		fileList =  os.listdir(directory)
		fileList = sorted(fileList)
		for f in fileList:
			fullPath = os.path.join(directory, f)
			m = re.match('.*/(\d*)-(.*)', fullPath, re.M | re.I | re.S)
			bno = ''
			bname = ''
			text = ''
			progno = ''
			if m:
				if not bankNumber:
					bno =  m.group(1).zfill(SnapshotConfigHandler.LEADING_ZERO_BANK)
					bname = m.group(2)
					text = bname
				else:
					text = os.path.splitext(m.group(2))[0]
					bno = bankNumber.zfill(SnapshotConfigHandler.LEADING_ZERO_BANK)
					bname = bankName
					progno = m.group(1).zfill(SnapshotConfigHandler.LEADING_ZERO_PROGRAM)
			snapshot = {
				'text': f,
				'name': text,
				'fullpath': fullPath,
				'id': idx,
				'bank': bno,
				'bankName': bname,
				'program': progno}
			idx+=1
			if os.path.isdir(os.path.join(directory, f)):
				snapshot['nodes'] = self.walkDirectory(os.path.join(directory, f), idx, bno, bname)
				idx+=len(snapshot['nodes'])
			snapshots.append(snapshot)

		return snapshots
