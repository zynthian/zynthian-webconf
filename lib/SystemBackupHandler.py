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
	BACKUP_ITEMS_FILE = "/zynthian/config/backup_items.txt"

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

		config['ZYNTHIAN_BACKUP_ITEMS'] = OrderedDict([])

		def addBackupItem( dirname, subdirs, files ):
			config['ZYNTHIAN_BACKUP_ITEMS'][dirname]=[]
			for filename in files:
				config['ZYNTHIAN_BACKUP_ITEMS'][dirname].append(filename)

		self.walk_backup_items(addBackupItem)

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="backup.html", config=config, title="Backup / Restore", errors=errors)


	def post(self):
		action = self.get_argument('ZYNTHIAN_BACKUP_ACTION')
		if action:
			errors = {
				'BACKUP': lambda: self.do_backup(),
				'RESTORE': lambda: self.do_restore()
			}[action]()

		self.get(errors)

	def do_backup(self):
		zipname="zynthian_backup.zip"
		f=BytesIO()
		zf = zipfile.ZipFile(f, "w")


		def backup_items(dirname, subdirs, files):
			zf.write(dirname)
			for filename in files:
				zf.write(os.path.join(dirname, filename))

		self.walk_backup_items(backup_items)

		zf.close()
		self.set_header('Content-Type', 'application/zip')
		self.set_header('Content-Disposition', 'attachment; filename=%s' % zipname)

		self.write(f.getvalue())
		f.close()
		self.finish()

	def do_restore(self):
		fileinfo = self.request.files['ZYNTHIAN_RESTORE_FILE'][0]
		restoreFile = fileinfo['filename']
		logging.debug("restoring: " + restoreFile)

		f=BytesIO(fileinfo['body'])
		validRestoreItems = self.get_backup_items()

		with zipfile.ZipFile(f,'r') as restoreZip:
			for member in restoreZip.namelist():
				if self.is_valid_restore_item(validRestoreItems, member):
					logging.debug("restoring: " + member)
					restoreZip.extract(member, "/")
				else:
					logging.warn("restore of " + member + " not permitted")
			restoreZip.close()
		f.close()

	def get_backup_items(self):
		with open(self.BACKUP_ITEMS_FILE) as f:
			return f.read().splitlines()

	def is_valid_restore_item(self, validRestoreItems, restoreMember):
		for validRestoreItem in validRestoreItems:
			if str("/" + restoreMember).startswith(os.path.expandvars(validRestoreItem)):
				return True
		return False

	def walk_backup_items(self, worker):
		for backupFolder in self.get_backup_items():
			try:
				sourceFolder = os.path.expandvars(backupFolder)
				for dirname, subdirs, files in os.walk(sourceFolder):
					worker(dirname, subdirs, files)
			except:
				pass
