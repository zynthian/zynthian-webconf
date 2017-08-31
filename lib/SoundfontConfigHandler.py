import os
import uuid
import re
import logging
import tornado.web
import json
import shutil
from collections import OrderedDict
from subprocess import check_output, call
from lib.ZynthianConfigHandler import ZynthianConfigHandler

#------------------------------------------------------------------------------
# Soundfont Configuration
#------------------------------------------------------------------------------

class SoundfontConfigHandler(tornado.web.RequestHandler):
	SOUNDFONTS_DIRECTORY = "/zynthian/zynthian-my-data/soundfonts"

	selectedTreeNode = 0
	selectedFullPath = '';

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

		soundfonts = self.walkDirectory(SoundfontConfigHandler.SOUNDFONTS_DIRECTORY, 0, '', '')

		config['ZYNTHIAN_SOUNDFONTS'] = json.dumps(soundfonts)

		config['ZYNTHIAN_SOUNDFONT_SELECTION_NODE_ID'] = self.selectedTreeNode


		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="soundfonts.html", config=config, title="Soundfonts", errors=errors)

	def post(self):
		action = self.get_argument('ZYNTHIAN_SOUNDFONT_ACTION')
		selectedFullPath =  self.get_argument('ZYNTHIAN_SOUNDFONT_FULLPATH')
		if action:
			errors = {
				'NEW': lambda: self.doNewBank(),
				'REMOVE': lambda: self.doRemove(),
				'SAVE': lambda: self.doSave(),
				'RENAME': lambda: self.doRename()
			}[action]()

		self.get(errors)

	def doSave(self):
		fileinfo = self.request.files['soundfontfile'][0]
		fname = fileinfo['filename']
		newFullPath = self.selectedFullPath + "/" + fname
		fh = open(newFullPath , 'w')
		logging.debug("uploading " + newFullPath)
		try:
			fh.write(str(fileinfo['body']))
		except:
			pass
		self.selectedFullPath = newFullPath;

	def doRemove(self):
		path = self.get_argument('ZYNTHIAN_SOUNDFONT_FULLPATH')
		try:
			if os.path.isdir(path):
				shutil.rmtree(path)
			else:
				os.remove(path)
		except:
			pass

	def doNewBank(self):
		if 	self.get_argument('ZYNTHIAN_SOUNDFONT_NEW_BANK_NAME'):
			os.mkdir( self.get_argument('ZYNTHIAN_SOUNDFONT_FULLPATH') + "/" + self.get_argument('ZYNTHIAN_SOUNDFONT_NEW_BANK_NAME'))

	def doRename(self):
		newName = ''

		if 	self.get_argument('ZYNTHIAN_SOUNDFONT_BANK_NAME'):
			newName = self.get_argument('ZYNTHIAN_SOUNDFONT_BANK_NAME')
		if self.get_argument('ZYNTHIAN_SOUNDFONT_NAME'):
			newName = self.get_argument('ZYNTHIAN_SOUNDFONT_NAME')
		if newName:
			sourceFolder = self.get_argument('ZYNTHIAN_SOUNDFONT_FULLPATH')
			m = re.match('(.*/)(.*)', sourceFolder, re.M | re.I | re.S)
			if m:
				destinationFolder = m.group(1) + newName
				shutil.move(sourceFolder, destinationFolder)
				self.selectedFullPath = destinationFolder;

	def walkDirectory(self, directory, idx, nodeType, soundfontType):
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
				if self.selectedFullPath == fullPath:
					self.selectedTreeNode = idx
			except:
				pass
			soundfont = {
				'text': f,
				'name': text,
				'fullpath': fullPath,
				'id': idx,
				'soundfontType': soundfontType,
				'nodeType': nextNodeType}
			idx+=1
			if os.path.isdir(os.path.join(directory, f)):
				soundfont['nodes'] = self.walkDirectory(os.path.join(directory, f), idx, nextNodeType, soundfontType)
				idx+=len(soundfont['nodes'])
			soundfonts.append(soundfont)
		#logging.info(soundfonts)
		return soundfonts
