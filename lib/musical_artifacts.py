# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Musical Artifacts Manager Handler
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
import sys
import logging
import requests
import bz2
import zipfile



#------------------------------------------------------------------------------
# Configure logging
#------------------------------------------------------------------------------

# Set root logging level
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

class MusicalArtifacts:
	ROOT_URL = 'https://musical-artifacts.com/artifacts.json'

	def search_artifacts(self, artifactFormat, tags):
		query = self.ROOT_URL
		querySeparator = '?'
		if artifactFormat:
			query += querySeparator + 'formats=' + artifactFormat
			querySeparator = "&"
		if tags:
			query += querySeparator + 'tags=' + tags
			querySeparator = "&"

		response = requests.get(query)
		searchResult = response.json()
		for row in searchResult:
			if not "file" in row and "mirrors" in row and len(row['mirrors'])>0:
				row['file'] = row['mirrors'][0]
			if not "file" in row:
				row['file'] = ''
		return searchResult

	def download_artifact(self, sourceFile, destinationFile, fileType, destinationFolder):
		r = requests.get(sourceFile)
		with open(destinationFile , "wb") as destFile:
			destFile.write(r.content)
			deleteDownloadedFile = False
			if destinationFile.endswith('.tar.bz2'):
				deleteDownloadedFile = True
				self.download_tar_bz2(destinationFile, fileType, destinationFolder)
			if destinationFile.endswith('.zip') or destinationFile.endswith('.7z'):
				deleteDownloadedFile = True
				self.download_zip(destinationFile, fileType, destinationFolder)
			if deleteDownloadedFile:
				os.remove(destinationFile)
			return destinationFile

	def download_tar_bz2(self, destinationFile, fileType, destinationFolder):
		tar = tarfile.open(destinationFile, "r:bz2")
		for member in tar.getmembers():
			if member.isfile():
				if member.name.endswith("." + fileType):
					member.name = os.path.basename(member.name)
					tar.extract(member, destinationFolder)
		tar.close()

	def download_zip(self, destinationFile, fileType, destinationFolder):
		with zipfile.ZipFile(destinationFile,'r') as soundfontZip:
			for member in soundfontZip.namelist():
				if member.endswith("." + fileType):
					soundfontZip.extract(member, destinationFolder)
			soundfontZip.close()
