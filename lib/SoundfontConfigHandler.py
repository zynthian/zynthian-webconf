import os
import uuid
import re
import logging
import tornado.web
import json
import shutil
import requests
import bz2
import zipfile
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
	searchResult = '';
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
		soundfonts = self.walkDirectory(SoundfontConfigHandler.SOUNDFONTS_DIRECTORY, '', '')

		config['ZYNTHIAN_SOUNDFONTS'] = json.dumps(soundfonts)

		config['ZYNTHIAN_SOUNDFONT_SELECTION_NODE_ID'] = self.selectedTreeNode

		config['ZYNTHIAN_SOUNDFONT_SEARCH_RESULT'] = self.searchResult

		try:
			config['ZYNTHIAN_SOUNDFONT_MUSICAL_ARTIFACT_TAGS'] = self.get_argument('ZYNTHIAN_SOUNDFONT_MUSICAL_ARTIFACT_TAGS')
		except:
			config['ZYNTHIAN_SOUNDFONT_MUSICAL_ARTIFACT_TAGS'] = ''

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="soundfonts.html", config=config, title="Soundfonts", errors=errors)

	def post(self):
		action = self.get_argument('ZYNTHIAN_SOUNDFONT_ACTION')
		self.selectedFullPath =  self.get_argument('ZYNTHIAN_SOUNDFONT_FULLPATH')
		if action:
			errors = {
				'NEW': lambda: self.doNewBank(),
				'REMOVE': lambda: self.doRemove(),
				'SAVE': lambda: self.doSave(),
				'RENAME': lambda: self.doRename(),
				'SEARCH': lambda: self.doSearch(),
				'DOWNLOAD': lambda: self.doDownload()
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
			newBank =  self.get_argument('ZYNTHIAN_SOUNDFONT_FULLPATH') + "/" + self.get_argument('ZYNTHIAN_SOUNDFONT_NEW_BANK_NAME')
			os.mkdir(newBank)
			self.selectedFullPath = newBank

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

	def doSearch(self):
		query = 'https://musical-artifacts.com/artifacts.json'
		querySeparator = '?'
		if self.get_argument('ZYNTHIAN_SOUNDFONT_SOUNDFONT_TYPE'):
			query += querySeparator + 'formats=' + self.get_argument('ZYNTHIAN_SOUNDFONT_SOUNDFONT_TYPE')
			querySeparator = "&"
		if self.get_argument('ZYNTHIAN_SOUNDFONT_MUSICAL_ARTIFACT_TAGS'):
			query += querySeparator + 'tags=' + self.get_argument('ZYNTHIAN_SOUNDFONT_MUSICAL_ARTIFACT_TAGS')
			querySeparator = "&"

		try:
			response = requests.get(query)
			self.searchResult = response.json()
			for row in self.searchResult:
				logging.info("row" + str(row))
				if not "file" in row and "mirrors" in row and len(row['mirrors'])>0:
					logging.info("taking first mirror")
					row['file'] = row['mirrors'][0]
				if not "file" in row:
					row['file'] = ''
		except OSError as err:
			logging.error(format(err))
			return format(err)

		logging.info(self.selectedFullPath)
		#logging.debug("searchResult: " + str(self.searchResult))

	def doDownload(self):
		if self.get_argument('ZYNTHIAN_SOUNDFONT_DOWNLOAD_FILE'):
			sourceFile = self.get_argument('ZYNTHIAN_SOUNDFONT_DOWNLOAD_FILE')
			logging.debug("downloading: " + sourceFile)
			r = requests.get(sourceFile)
			m = re.match('(.*/)(.*)', sourceFile, re.M | re.I | re.S)
			if m:
				destinationFile = self.selectedFullPath + "/" + m.group(2)
				with open(destinationFile , "wb") as soundfontFile:
					soundfontFile.write(r.content)
					deleteDownloadedFile = False
					if destinationFile.endswith('.tar.bz2'):
						deleteDownloadedFile = True
						self.downloadTarBz2(destinationFile)
					if destinationFile.endswith('.zip') or destinationFile.endswith('.7z'):
						deleteDownloadedFile = True
						self.downloadZip(destinationFile)
					if deleteDownloadedFile:
						os.remove(destinationFile)
					self.cleanupDownload(self.selectedFullPath, self.selectedFullPath)

					self.selectedFullPath = destinationFile

	def downloadTarBz2(self, destinationFile):
		tar = tarfile.open(destinationFile, "r:bz2")
		for member in tar.getmembers():
			if member.isfile():
				if member.name.endswith("." + self.get_argument('ZYNTHIAN_SOUNDFONT_SOUNDFONT_TYPE')):
					member.name = os.path.basename(member.name)
					tar.extract(member, self.selectedFullPath)
		tar.close()

	def downloadZip(self, destinationFile):
		with zipfile.ZipFile(destinationFile,'r') as soundfontZip:
			for member in soundfontZip.namelist():
				if member.endswith("." + self.get_argument('ZYNTHIAN_SOUNDFONT_SOUNDFONT_TYPE')):
					soundfontZip.extract(member, self.selectedFullPath)
			soundfontZip.close()

	def cleanupDownload(self, currentDirectory, targetDirectory):
		logging.info("currentDirectory" + currentDirectory)
		fileList =  os.listdir(currentDirectory)
		for f in fileList:

			sourcePath = os.path.join(currentDirectory, f)
			logging.info("sourcePath" + sourcePath)

			if os.path.isdir(sourcePath):
				self.cleanupDownload(sourcePath, targetDirectory)
				shutil.rmtree(sourcePath)
			else:
				if not f.startswith(".") and  f.endswith("." + self.get_argument('ZYNTHIAN_SOUNDFONT_SOUNDFONT_TYPE')):
					targetPath = os.path.join(targetDirectory, f)
					shutil.move(sourcePath, targetPath)


	def walkDirectory(self, directory, nodeType, soundfontType):
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
				soundfont['nodes'] = self.walkDirectory(os.path.join(directory, f), nextNodeType, soundfontType)

			soundfonts.append(soundfont)
		#logging.info(soundfonts)
		return soundfonts
