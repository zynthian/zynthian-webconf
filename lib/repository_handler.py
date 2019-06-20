# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Audio Configuration Handler
#
# Copyright (C) 2017 Fernando Moyano <jofemodo@zynthian.org>
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
import tornado.web
from collections import OrderedDict
from subprocess import check_output, call

from lib.zynthian_config_handler import ZynthianConfigHandler
from lib.audio_config_handler import AudioConfigHandler
from lib.display_config_handler import DisplayConfigHandler
from lib.wiring_config_handler import WiringConfigHandler

#------------------------------------------------------------------------------
# GIT Repository Configuration
#------------------------------------------------------------------------------

class RepositoryHandler(ZynthianConfigHandler):

	repository_list = [
		'zyncoder',
		'zynthian-ui',
		'zynthian-sys',
		'zynthian-data',
		'zynthian-webconf'
	]

	@tornado.web.authenticated
	def get(self, errors=None):



		config = OrderedDict([])

		for repository_name in self.repository_list:
			tag_list = self.get_tag_list(repository_name)
			config['ZYNTHIAN_REPO_%s' % repository_name] = {
				'type': 'select',
				'title': repository_name,
				'value': self.get_current_branch(repository_name),
				'options': tag_list,
				'option_labels': OrderedDict([(tag_name, tag_name) for tag_name in tag_list])
			}

		super().get("Repositories", config, errors)


	@tornado.web.authenticated
	def post(self):
		postedConfig = tornado.escape.recursive_unicode(self.request.arguments)

		logging.info(postedConfig)
		for posted_config_key in postedConfig:
			repository_name = posted_config_key[14:]
			logging.info(repository_name)
			self.update_branch(repository_name, postedConfig[posted_config_key][0])

		errors = {}
		self.get(errors)

		return errors

	def get_tag_list(self, repository_name):
		result = []
		result.append('master')

		for byteLine in check_output("cd /zynthian/%s; git tag" % repository_name, shell=True).splitlines():
			result.append(byteLine.decode("utf-8"))

		return result

	def get_current_branch(self, repository_name):
		for byteLine in check_output("cd /zynthian/%s; git branch | grep \* | cut -d ' ' -f2" % repository_name, shell=True).splitlines():
			return byteLine.decode("utf-8")

	def update_branch(self, repository_name, new_branch_name):
		current_branch = self.get_current_branch(repository_name)
		if new_branch_name != current_branch:
			logging.info("needs change %s != %s" % (current_branch, new_branch_name))
			if new_branch_name == 'master':
				check_output("cd /zynthian/%s; git checkout %s" % (repository_name, new_branch_name), shell=True)
			else:
				check_output("cd /zynthian/%s; git branch -d %s;git checkout tags/%s -b %s" % (repository_name, new_branch_name, new_branch_name, new_branch_name), shell=True)