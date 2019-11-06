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
			result = {
				'get_tree': lambda: self.do_get_tree(),
				'new_bank': lambda: self.do_new_bank(),
				'remove_bank': lambda: self.do_remove_bank(),
				'rename_bank': lambda: self.do_rename_bank(),
				'remove_preset': lambda: self.do_remove_preset(),
				'rename_preset': lambda: self.do_rename_preset(),
				'download': lambda: self.do_download(),
				'search': lambda: self.do_search(),
				'install': lambda: self.do_install(),
				'upload': lambda: self.do_upload()
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
		result = {}
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
	
			if delete:
				os.remove(fpath)

			return None

		except Exception as e:
			logging.error(e)
			result['errors'] = "Can't download file: {}".format(e)

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


	def do_install(self):
		result = {}

		try:
			self.install_url(self.get_argument('INSTALL_URL'))
		except Exception as e:
			logging.error(e)
			result['errors'] = "Can't install URL: {}".format(e)

		result.update(self.do_get_tree())
		return result


	def search_artifacts(self, formats, tags):
		query_url = "https://musical-artifacts.com/artifacts.json"
		sep = '?'
		if formats:
			query_url += sep + 'formats=' + formats
			sep = "&"
		if tags:
			query_url += sep + 'tags=' + tags
			sep = "&"

		result = requests.get(query_url, verify=False).json()
		for row in result:
			if not "file" in row and "mirrors" in row and len(row['mirrors'])>0:
				row['file'] = row['mirrors'][0]
			if not "file" in row:
				row['file'] = ''

		return result


	def install_file(self, fpath):
		logging.info("Unpacking '{}' ...".format(fpath))
		if fpath.endswith('.tar.bz2'):
			dpath = fpath[:-8]
			tar = tarfile.open(fpath, "r:bz2")
			tar.extractall(dpath)
			os.remove(fpath)
		elif fpath.endswith('.tar.gz'):
			dpath = fpath[:-7]
			tar = tarfile.open(fpath, "r:gz")
			tar.extractall(dpath)
			os.remove(fpath)
		elif fpath.endswith('.tgz'):
			dpath = fpath[:-4]
			tar = tarfile.open(fpath, "r:gz")
			tar.extractall(dpath)
			os.remove(fpath)
		elif fpath.endswith('.zip'):
			dpath = fpath[:-4]
			with zipfile.ZipFile(fpath,'r') as soundfontZip:
				soundfontZip.extractall(dpath)
			os.remove(fpath)
		else:
			dpath = fpath

		logging.info("Installing '{}' ...".format(dpath))
		self.engine_cls.zynapi_install(dpath, self.get_argument('SEL_BANK_FULLPATH'))


	def install_url(self, url):
		logging.info("Downloading '{}' ...".format(url))
		res = requests.get(url, verify=False)
		head, tail = os.path.split(url)
		fpath = "/tmp/" + tail
		with open(fpath , "wb") as df:
			df.write(res.content)
			df.close()
			self.install_file(fpath)


	def do_upload(self):
		try:
			new_upload_file = self.get_argument('UPLOAD_FILE','')
			if new_upload_file:
				filename_parts = os.path.splitext(new_upload_file)
				self.selected_full_path = self.revise_filename(os.path.dirname(new_upload_file), new_upload_file, filename_parts[1][1:])
		except Exception as err:
			logging.error(format(err))
			return format(err)


	def revise_filename(self, selected_full_path, downloaded_file, file_type):
		m = re.match('.*/(\d*)-{0,1}(.*)', downloaded_file, re.M | re.I | re.S)
		if m:
			filename =  m.group(2)

			file_list =  os.listdir(selected_full_path)
			file_list = sorted(file_list)

			existing_program_numbers = []
			for f in file_list:
				if downloaded_file != selected_full_path + "/" + f:
					# logging.info(f)
					fp = os.path.join(selected_full_path, f)
					m3 = re.match('.*/(\d*)-{0,1}(.*)', fp, re.M | re.I | re.S)
					if m3:
						try:
							existing_program_numbers.append(int(m3.group(1)))
						except:
							pass
			# logging.info(existing_program_numbers)

			if  m.group(1) and not int(m.group(1)) in existing_program_numbers:
				current_index = int(m.group(1))
			else:
				current_index = 0
				for existing_program_number in existing_program_numbers:
					if existing_program_number != current_index:
						current_index +=1
						break
					current_index +=1

			shutil.move(downloaded_file,selected_full_path + "/" + str(current_index).zfill(4 + "-" + filename))


	def get_engine_info(self):
		engine_info = copy.copy(zynthian_gui_engine.engine_info)
		for e in zynthian_gui_engine.engine_info:
			if not hasattr(engine_info[e][3], "zynapi_get_banks"):
				del engine_info[e]
		return engine_info


	def get_upload_formats(self):
		if self.engine_cls==zynthian_engine_jalv:
			self.engine_cls.init_zynapi_instance(self.engine_info[0], self.engine_info[2])

		try:
			return self.engine_cls.zynapi_get_formats()
		except:
			return ""


	def get_presets_data(self):
		if self.engine_cls==zynthian_engine_jalv:
			self.engine_cls.init_zynapi_instance(self.engine_info[0], self.engine_info[2])

		try:
			i = 0
			banks_data = []
			for b in self.engine_cls.zynapi_get_banks():
				brow = {
					'id': i,
					'text': b['text'],
					'name': b['name'],
					'fullpath': b['fullpath'],
					'node_type': 'BANK',
					'nodes': []
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
							'bank_fullpath' : b['fullpath'],
							'node_type': 'PRESET',
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

