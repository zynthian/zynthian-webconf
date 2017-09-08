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


#------------------------------------------------------------------------------
# Snapshot Config Handler
#------------------------------------------------------------------------------

class SystemBackupHandler(tornado.web.RequestHandler):

	backupFolders=[
		"${ZYNTHIAN_SW_DIR}/mod-ui/dados/favorites.json",
		"${ZYNTHIAN_MY_PLUGINS_DIR}",
		"${ZYNTHIAN_MY_DATA_DIR}"
	]

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


		config['ZYNTHIAN_BACKUP_FOLDERS'] = self.backupFolders

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="backup.html", config=config, title="Backup / Restore", errors=errors)


	def post(self):
		action = self.get_argument('ZYNTHIAN_BACKUP_ACTION')
		if action:
			errors = {
				'BACKUP': lambda: self.doBackup(),
				'RESTORE': lambda: self.doRestore()
			}[action]()

		self.get(errors)

	def doBackup(self):
		zipname="zynthian_backup.zip"
		f=BytesIO()
		zf = zipfile.ZipFile(f, "w")

		for backupFolder in self.backupFolders:
			try:
				sourceFolder = os.path.expandvars(backupFolder)
				logging.info("backup up: " + sourceFolder)
				for dirname, subdirs, files in os.walk(sourceFolder):
					 zf.write(dirname)
					 for filename in files:
						 zf.write(os.path.join(dirname, filename))
			except:
				pass
		zf.close()
		self.set_header('Content-Type', 'application/zip')
		self.write(f.getvalue())
		f.close()
		self.finish()

	def doRestore(self):
		fileinfo = self.request.files['ZYNTHIAN_RESTORE_FILE'][0]
		restoreFile = fileinfo['filename']
		logging.debug("restoring: " + restoreFile)

		f=BytesIO(fileinfo['body'])

		with zipfile.ZipFile(f,'r') as restoreZip:
			for member in restoreZip.namelist():
				logging.debug(member)
				restoreZip.extract(member, "/")
			restoreZip.close()
		f.close()
