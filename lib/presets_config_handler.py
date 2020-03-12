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
import copy
import uuid
import urllib3
import logging
import shutil
import requests
import bz2
import zipfile
import tarfile
import tornado.web
from collections import OrderedDict

from lib.zynthian_config_handler import ZynthianConfigHandler
from zyngui.zynthian_gui_engine import *

#------------------------------------------------------------------------------
# Soundfont Configuration
#------------------------------------------------------------------------------

class PresetsConfigHandler(ZynthianConfigHandler):

	@tornado.web.authenticated
	def get(self):
		config=OrderedDict([])

		config['engines'] = self.get_engine_info()
		config['engine'] = self.get_argument('ENGINE', 'ZY')
		config['sel_node_id'] = self.get_argument('SEL_NODE_ID', -1)
		config['musical_artifact_tags'] = self.get_argument('MUSICAL_ARTIFACT_TAGS', '')
		config['ZYNTHIAN_UPLOAD_MULTIPLE'] = True

		if self.genjson:
			self.write(config)
		else:
			self.render("config.html", body="presets.html", config=config, title="Presets & Soundfonts", errors=None)


	@tornado.web.authenticated
	def post(self, action):
		try:
			self.engine = self.get_argument('ENGINE', 'ZY')
			self.engine_info = zynthian_gui_engine.engine_info[self.engine]
			self.engine_cls = self.engine_info[3]
			if self.engine_cls==zynthian_engine_jalv:
				self.engine_cls.init_zynapi_instance(self.engine_info[0], self.engine_info[2])

		except Exception as e:
			logging.error("Can't initialize engine '{}': {}".format(self.engine,e))

		try:
			result = {
				'get_tree': lambda: self.do_get_tree(),
				'new_bank': lambda: self.do_new_bank(),
				'remove_bank': lambda: self.do_remove_bank(),
				'rename_bank': lambda: self.do_rename_bank(),
				'remove_preset': lambda: self.do_remove_preset(),
				'rename_preset': lambda: self.do_rename_preset(),
				'download': lambda: self.do_download(),
				'search': lambda: self.do_search(),
				'install': lambda: self.do_install_url(),
				'upload': lambda: self.do_install_file()
			}[action]()

		except:
			result = {}

		# JSON Ouput
		if result:
			self.write(result)


	def do_get_tree(self):
		result = {}
		try:
			result['methods'] =	self.engine_cls.get_zynapi_methods()
			result['formats'] =	self.get_upload_formats()
			result['presets'] = self.get_presets_data()
		except Exception as e:
			result['methods'] =  None
			result['formats'] =  None
			result['presets'] = None
			logging.error(e)
			result['errors'] = "Can't get preset tree data: {}".format(e)

		return result


	def do_new_bank(self):
		result = {}
		try:
			self.engine_cls.zynapi_new_bank(self.get_argument('NEW_BANK_NAME'))
		except Exception as e:
			logging.error(e)
			result['errors'] = "Can't create new bank: {}".format(e)

		result.update(self.do_get_tree())
		return result


	def do_rename_bank(self):
		result = {}
		try:
			self.engine_cls.zynapi_rename_bank(self.get_argument('SEL_FULLPATH'), self.get_argument('SEL_BANK_NAME'))
		except Exception as e:
			logging.error(e)
			result['errors'] = "Can't rename bank: {}".format(e)

		result.update(self.do_get_tree())
		return result


	def do_remove_bank(self):
		result = {}
		try:
			self.engine_cls.zynapi_remove_bank(self.get_argument('SEL_FULLPATH'))
		except Exception as e:
			logging.error(e)
			result['errors'] = "Can't remove bank: {}".format(e)

		result.update(self.do_get_tree())
		return result


	def do_rename_preset(self):
		result = {}
		try:
			self.engine_cls.zynapi_rename_preset(self.get_argument('SEL_FULLPATH'), self.get_argument('SEL_PRESET_NAME'))
		except Exception as e:
			logging.error(e)
			result['errors'] = "Can't rename preset: {}".format(e)

		result.update(self.do_get_tree())
		return result


	def do_remove_preset(self):
		result = {}
		try:
			self.engine_cls.zynapi_remove_preset(self.get_argument('SEL_FULLPATH'))
		except Exception as e:
			logging.error(e)
			result['errors'] = "Can't remove preset: {}".format(e)

		result.update(self.do_get_tree())
		return result


	def do_download(self):
		result = None
		fpath = None
		delete = False
		try:
			fpath=self.engine_cls.zynapi_download(self.get_argument('SEL_FULLPATH'))
			dname, fname = os.path.split(fpath)
			if os.path.isdir(fpath):
				zfpath = "/tmp/" + fname
				shutil.make_archive(zfpath, 'zip', fpath)
				fpath = zfpath + ".zip"
				fname += ".zip"
				delete = True
				mime_type = "application/zip"
			else:
				delete = False
				mime_type = "application/octet-stream"

			self.set_header('Content-Type', mime_type)
			self.set_header("Content-Description", "File Transfer")
			self.set_header('Content-Disposition', 'attachment; filename="{}"'.format(fname))
			with open(fpath, 'rb') as f:
				while True:
					data = f.read(4096)
					if not data:
						break
					self.write(data)
				self.finish()
	
		except Exception as e:
			logging.error(e)
			result = {}
			result['errors'] = "Can't download file: {}".format(e)

		finally:
			if fpath and delete:
				os.remove(fpath)

		return result


	def do_search(self):
		result = {}

		try:
			maformats = self.engine_cls.zynapi_martifact_formats()
			result['search_results'] = self.search_artifacts(maformats, self.get_argument('MUSICAL_ARTIFACT_TAGS'))
		except OSError as e:
			logging.error(e)
			result['errors'] = "Can't search Musical Artifacts: {}".format(e)

		return result


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

		result.update(self.do_get_tree())
		return result


	def do_install_url(self):
		result = {}

		try:
			self.install_url(self.get_argument('INSTALL_URL'))
		except Exception as e:
			logging.error(e)
			result['errors'] = "Can't install URL: {}".format(e)

		result.update(self.do_get_tree())
		return result


	def search_artifacts(self, formats, tags):
		result=[]
		for fmt in formats.split(','):
			query_url = "https://musical-artifacts.com/artifacts.json"
			sep = '?'
			if formats:
				query_url += sep + 'formats=' + fmt
				sep = "&"
			if tags:
				query_url += sep + 'tags=' + tags
				#query_url += sep + 'q=' + tags
				sep = "&"

			result += requests.get(query_url, verify=False).json()

		for row in result:
			if not "file" in row:
				if "mirrors" in row and len(row['mirrors'])>0:
					row['file'] = row['mirrors'][0]
				else:
					row['file'] = None

		return result


	def install_file(self, fpath):
		logging.info("Unpacking '{}' ...".format(fpath))
		dpath = fpath
		try:
			if fpath.endswith('.tar.bz2'):
				dpath = fpath[:-8]
				tar = tarfile.open(fpath, "r:bz2")
				tar.extractall(dpath)
			elif fpath.endswith('.tar.gz'):
				dpath = fpath[:-7]
				tar = tarfile.open(fpath, "r:gz")
				tar.extractall(dpath)
			elif fpath.endswith('.tgz'):
				dpath = fpath[:-4]
				tar = tarfile.open(fpath, "r:gz")
				tar.extractall(dpath)
			elif fpath.endswith('.zip'):
				dpath = fpath[:-4]
				with zipfile.ZipFile(fpath,'r') as soundfontZip:
					soundfontZip.extractall(dpath)

			# Remove thrash ...
			if os.path.isdir(dpath):
				shutil.rmtree(dpath + "/__MACOSX", ignore_errors=True)

			bank_fullpath = self.get_argument('SEL_BANK_FULLPATH')
			logging.info("Installing '{}' => '{}' ...".format(dpath, bank_fullpath))

			self.engine_cls.zynapi_install(dpath, bank_fullpath)

		finally:
			try:
				os.remove(fpath)
			except:
				pass
			shutil.rmtree(dpath, ignore_errors=True)
			pass


	def install_url(self, url):
		logging.info("Downloading '{}' ...".format(url))
		res = requests.get(url, verify=False)
		head, tail = os.path.split(url)
		fpath = "/tmp/" + tail
		with open(fpath , "wb") as df:
			df.write(res.content)
			df.close()
			self.install_file(fpath)


	def get_engine_info(self):
		engine_info = copy.copy(zynthian_gui_engine.engine_info)
		for e in zynthian_gui_engine.engine_info:
			if not engine_info[e][4] or not hasattr(engine_info[e][3], "zynapi_get_banks"):
				del engine_info[e]
		return engine_info


	def get_upload_formats(self):
		try:
			return self.engine_cls.zynapi_get_formats()
		except:
			return ""


	def get_presets_data(self):
		try:
			i = 0
			banks_data = []
			for b in self.engine_cls.zynapi_get_banks():
				brow = {
					'id': i,
					'text': b['text'],
					'name': b['name'],
					'fullpath': b['fullpath'],
					'readonly': b['readonly'],
					'node_type': 'BANK',
					'nodes': [],
					'icon': "glyphicon glyphicon-link" if b['readonly'] else None,
				}
				i += 1
				try:
					presets_data = []
					for p in self.engine_cls.zynapi_get_presets(b):
						prow = {
							'id': i,
							'text': p['text'],
							'name': p['name'],
							'fullpath': p['fullpath'],
							'readonly': p['readonly'] or b['readonly'],
							'bank_fullpath' : b['fullpath'],
							'node_type': 'PRESET',
							'icon': "glyphicon glyphicon-link" if p['readonly'] else None
						}
						i += 1
						presets_data.append(prow)

					brow['nodes'] = presets_data

				except Exception as e:
					logging.error("PRESET NODE {} => {}".format(i,e))

				banks_data.append(brow)

		except Exception as e:
			logging.error("BANK NODE {} => {}".format(i,e))

		return banks_data

