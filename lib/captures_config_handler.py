# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Presets Manager Handler
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
import shutil
import mutagen
import fnmatch
import logging
import jsonpickle
import subprocess
import tornado.web
from zipfile import ZipFile
from collections import OrderedDict
from lib.zynthian_config_handler import ZynthianBasicHandler

#------------------------------------------------------------------------------
# Soundfont Configuration
#------------------------------------------------------------------------------

class CapturesConfigHandler(ZynthianBasicHandler):
	CAPTURES_DIRECTORY = "/zynthian/zynthian-my-data/capture"
	MOUNTED_CAPTURES_DIRECTORY = "/media/usb0"

	selectedTreeNode = 0
	selected_full_path = ''
	searchResult = ''
	maxTreeNodeIndex = 0

	@tornado.web.authenticated
	def get(self, errors=None):
		config=OrderedDict([])
		self.maxTreeNodeIndex = 0
		if self.get_argument('stream', None, True):
			self.do_download(self.get_argument('stream').replace("%27","'"))
		else:
			captures = []
			captures.append(self.create_node('wav'))
			captures.append(self.create_node('ogg'))
			captures.append(self.create_node('mp3'))
			captures.append(self.create_node('mid'))
			captures.append(self.create_node('log'))

			config['ZYNTHIAN_CAPTURES'] = json.dumps(captures)
			config['ZYNTHIAN_CAPTURES_SELECTION_NODE_ID'] = self.selectedTreeNode | 0
			config['ZYNTHIAN_UPLOAD_MULTIPLE'] = True

			super().get("captures.html", "Captures", config, errors)


	def post(self):
		action = self.get_argument('ZYNTHIAN_CAPTURES_ACTION', None)
		if not action and self.get_argument('INSTALL_FPATH', None):
			action = 'UPLOAD'
		self.selected_full_path = self.get_argument('ZYNTHIAN_CAPTURES_FULLPATH').replace("%27","'")
		if action:
			errors = {
				'REMOVE': lambda: self.do_remove(),
				'RENAME': lambda: self.do_rename(),
				'DOWNLOAD': lambda: self.do_download(self.get_argument('ZYNTHIAN_CAPTURES_FULLPATH')),
				'CONVERT_OGG': lambda: self.do_convert_ogg(),
				'UPLOAD': lambda: self.do_install_file(),
				'SAVE_LOG': lambda: self.do_save_log()
			}[action]()

		if (action not in ('DOWNLOAD', 'SAVE_LOG')):
			self.get(errors)


	def do_remove(self):
		logging.info("Removing {}".format(self.selected_full_path))
		try:
			if os.path.isdir(self.selected_full_path):
				shutil.rmtree(self.selected_full_path)
			else:
				os.remove(self.selected_full_path)
				fparts = os.path.splitext(self.selected_full_path)
				if fparts[1] == ".log":
					video_fpath = fparts[0] + ".mp4"
					logging.info("Removing capture log video: {} ".format(video_fpath))
					os.remove(video_fpath)
		except:
			pass


	def do_rename(self):
		if self.get_argument('ZYNTHIAN_CAPTURES_RENAME'):
			rename = self.get_argument('ZYNTHIAN_CAPTURES_RENAME')
		else:
			logging.error("Can't rename: No destination file name")
			return

		if self.get_argument('ZYNTHIAN_CAPTURES_NAME'):
			fparts = os.path.splitext(self.get_argument('ZYNTHIAN_CAPTURES_NAME'))
			fname = fparts[0]
			fext = fparts[1]
		else:
			logging.error("Can't rename: No origin file name")
			return

		if self.get_argument('ZYNTHIAN_CAPTURES_FULLPATH'):
			src_fpath = self.get_argument('ZYNTHIAN_CAPTURES_FULLPATH')
			parts = os.path.split(src_fpath)
			dirpath = parts[0]
		else:
			logging.error("Can't rename: No destination directory")
			return

		if dirpath:
			title = rename
			rename = rename.replace(" ", "_")
			dest_fpath = dirpath + "/" + rename + fext
			logging.info("Renaming capture: {} => {}".format(src_fpath, dest_fpath))
			shutil.move(src_fpath, dest_fpath)
			self.selected_full_path = dest_fpath
			# When renaming log files, change title inside log file and rename associated video file (mp4)
			if fext == ".log":
				self.set_log_title(dest_fpath, title)
				src_fpath = dirpath + "/" + fname + ".mp4"
				dest_fpath = dirpath + "/" + rename + ".mp4"
				logging.info("Renaming capture log video: {} => {}".format(src_fpath, dest_fpath))
				shutil.move(src_fpath, dest_fpath)


	def do_download(self, fullpath):
		if fullpath:
			fparts = os.path.split(fullpath)
			dirpath = fparts[0]
			filename = fparts[1]

			# If file is a capture log, generate download package with log + video
			fparts = os.path.splitext(filename)
			if fparts[1] == ".log":
				filename = fparts[0] + ".zip"
				fullpath = "/tmp/" + filename
				with ZipFile(fullpath, 'w') as tmpzip:
					tmpzip.write(dirpath + "/" + fparts[0] + ".log", fparts[0] + ".log")
					tmpzip.write(dirpath + "/" + fparts[0] + ".mp4", fparts[0] + ".mp4")

			with open(fullpath, 'rb') as f:
				try:
					while True:
						data = f.read(4096)
						if not data:
							break
						self.write(data)

					self.set_header('Content-Type', self.get_content_type(filename))
					self.set_header('Content-Disposition', 'attachment; filename="%s"' % filename)
					self.finish()
				except Exception as exc:
					logging.error(exc)
					self.set_header('Content-Type', 'application/json')
					self.write(jsonpickle.encode({'data': format(exc)}))


	def do_install_file(self):
		result = {}
		try:
			for fpath in self.get_argument('INSTALL_FPATH').split(","):
				fpath = fpath.strip()
				if len(fpath)>0:
					self.install_file(fpath)
		except Exception as e:
			logging.error(e)
			result['errors'] = "Can't install file: {}".format(e)

		return result


	def do_convert_ogg(self):
		ogg_file_name = os.path.splitext(self.selected_full_path)[0]+'.ogg'
		cmd = 'oggenc "{}" -o "{}"'.format(self.selected_full_path, ogg_file_name)
		try:
			logging.info(cmd)
			subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
		except Exception as e:
			return e.output
		return


	def do_save_log(self):
		capture_log = self.get_argument('ZYNTHIAN_CAPTURES_LOG_CONTENT')
		logging.info("Saving capture log => {}".format(capture_log))
		capture_log_lines = capture_log.split("\n")
		capture_log_title = None
		for line in capture_log_lines:
			parts = line.split(" ", 1)
			if parts[1].startswith("TITLE: "):
				capture_log_title = parts[1][7:]
				break
		if capture_log_title:
			fname = capture_log_title.replace(" ", "_")
		else:
			fname = self.get_argument('ZYNTHIAN_CAPTURES_LOG_FNAME')

		if fname:
			fpath = CapturesConfigHandler.CAPTURES_DIRECTORY + "/" + fname + ".log"
			logging.info("Saving capture log to '{}'".format(fpath))
			try:
				f = open(fpath, "w")
				f.write(capture_log)
				f.close()
			except:
				logging.error("Can't write capture log file")
		else:
			logging.error("Can't save capture log: No file name")


	def set_log_title(self, fpath, title):
		logging.info("Setting capture log '{}' title to '{}'".format(fpath, title))

		try:
			f = open(fpath, "r")
			capture_log = f.read()
			f.close()
		except:
			logging.error("Can't read capture log file")
			return

		capture_log_lines = capture_log.split("\n")
		for i, line in enumerate (capture_log_lines):
			parts = line.split(" ", 1)
			if parts[1].startswith("TITLE: "):
				capture_log_lines[i] = parts[0] + " TITLE: " + title
				break

		capture_log = "\n".join(capture_log_lines)
		try:
			f = open(fpath, "w")
			f.write(capture_log)
			f.close()
		except:
			logging.error("Can't write capture log file")


	def get_content_type(self, filename):
		fext = os.path.splitext(filename)[1].lower()
		if fext == '.mid':
			return 'audio/midi'
		elif fext == '.ogg':
			return 'audio/ogg'
		elif fext == '.mp3':
			return 'audio/mp3'
		elif fext == '.wav':
			return 'application/wav'
		elif fext == '.mp4':
			return 'video/mp4'
		elif fext == '.log':
			return 'text/plain'
		elif fext == '.zip':
			return 'application/zip'

	def create_node(self, file_extension):
		captures = []
		root_capture = {
			'text': file_extension,
			'name': file_extension,
			'fullpath': 'ignore',
			'icon': '',
			'id': self.maxTreeNodeIndex
		}
		self.maxTreeNodeIndex += 1

		try:
			if os.path.ismount(CapturesConfigHandler.MOUNTED_CAPTURES_DIRECTORY):
				captures.extend(
					self.walk_directory(CapturesConfigHandler.MOUNTED_CAPTURES_DIRECTORY, 'fa fa-fw fa-usb', file_extension))
			else:
				logging.info("/media/usb0 not found")
		except:
			pass

		try:
			captures.extend(self.walk_directory(CapturesConfigHandler.CAPTURES_DIRECTORY, 'fa fa-fw fa-file', file_extension))
		except:
			pass
		root_capture['nodes'] = captures
		return root_capture

	def install_file(self, fpath):
		logging.info(fpath)
		fname, fext = os.path.splitext(os.path.basename(fpath))

		destination = "{}/{}.{}".format(CapturesConfigHandler.CAPTURES_DIRECTORY, fname, fext[1:4])
		logging.info(destination)
		shutil.move(fpath, destination)

	def walk_directory(self, directory, icon, file_extension):
		captures = []
		logging.info("Getting {} filelist from {}".format(file_extension,directory))
		for f in sorted(os.listdir(directory)):

			fname, fext = os.path.splitext(f)
			if len(fext)>0:
				fext = fext[1:] 

			#logging.debug("{} => {}".format(fname,fext))

			if fext.lower()!=file_extension.lower():
				continue

			fullPath = os.path.join(directory, f)
			logging.debug(fullPath)
			#m = re.match('.*/(.*)', fullPath, re.M | re.I | re.S)
			#text = ''
			#if m:
			#	text = m.group(1)

			try:
				if self.selected_full_path == fullPath:
					self.selectedTreeNode = self.maxTreeNodeIndex # max is current right now
			except:
				pass

			text = f.replace("'", "&#39;")
			try:
				l = mutagen.File(fullPath).info.length
				text = "{} [{}:{:02d}]".format(f.replace("'", "&#39;"), int(l/60), int(l%60))
			except Exception as e:
				logging.warning(e)

			capture = {
				'text': text,
				'name': f.replace("'","&#39;"),
				'fext': fext,
				'fullpath': fullPath.replace("'","&#39;"),
				'icon': icon,
				'id': self.maxTreeNodeIndex
			}
			self.maxTreeNodeIndex+=1
			if os.path.isdir(fullPath):
				capture['nodes'] = self.walk_directory(os.path.join(directory, f), icon)
			captures.append(capture)



		return captures
