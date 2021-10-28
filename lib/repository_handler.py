# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Audio Configuration Handler
#
# Copyright (C) 2017 Fernando Moyano <jofemodo@zynthian.org>
#
# ********************************************************************
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
# ********************************************************************

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


# ------------------------------------------------------------------------------
# GIT Repository Configuration
# ------------------------------------------------------------------------------

class RepositoryHandler(ZynthianConfigHandler):
	zynthian_base_dir = os.environ.get('ZYNTHIAN_DIR', "/zynthian")

	repository_list = [
		['zynthian-ui', True],
		['zynthian-webconf', True],
		['zynthian-sys', True],
		['zynthian-data', True],
		['zyncoder', True]
	]

	@tornado.web.authenticated
	def get(self, errors=None):
		super().get("Repositories", self.get_config_info(), errors)

	@tornado.web.authenticated
	def post(self):
		postedConfig = tornado.escape.recursive_unicode(self.request.arguments)
		logging.info(postedConfig)

		errors = {}
		changed_repos = 0
		try:
			is_stable = (postedConfig['TESTING'][0] == '0')
		except:
			is_stable = True
		for posted_config_key in postedConfig:
			repo_name = posted_config_key[14:]
			try:
				branch = postedConfig[posted_config_key][0]
				if is_stable:
					if self.set_repo_branch(repo_name, 'stable'):
						changed_repos += 1
				else:
					if branch == 'stable':
						branch = 'testing'
					if self.set_repo_branch(repo_name, branch):
						changed_repos += 1
			except Exception as err:
				logging.error(err)
				errors["ZYNTHIAN_REPO_{}".format(repo_name)] = err

		config = self.get_config_info()
		if changed_repos > 0:
			config['ZYNTHIAN_MESSAGE'] = {
				'type': 'html',
				'content': "<div class='alert alert-success'>Some repo changed its branch. You may want to <a href='/sw-update'>update the software</a> for getting the latest changes.</div>"
			}

		super().get("Repositories", config, errors)

	def get_config_info(self):
		config = OrderedDict([])
		config["TESTING"] = {
			'type': 'boolean',
			'title': 'Testing',
			'value': '0',
			'advanced': False
		}
		testing_overall = False
		for repitem in self.repository_list:
			options = self.get_repo_branch_list(repitem[0])
			config["ZYNTHIAN_REPO_{}".format(repitem[0])] = {
				'type': 'select',
				'title': repitem[0],
				'value': self.get_repo_current_branch(repitem[0]),
				'options': options,
				'option_labels': OrderedDict([(opt, opt) for opt in options]),
				'advanced': repitem[1]
			}
			testing_overall |= (self.get_repo_current_branch(repitem[0]) != 'stable')
		config["TESTING"]['value'] = '1' if testing_overall else '0'
		return config

	def get_repo_tag_list(self, repo_name):
		result = ["master"]
		repo_dir = self.zynthian_base_dir + "/" + repo_name

		check_output("cd {}; git remote update origin --prune".format(repo_dir), shell=True)
		for byteLine in check_output("cd {}; git tag".format(repo_dir), shell=True).splitlines():
			result.append(byteLine.decode("utf-8").strip())

		return result

	def get_repo_branch_list(self, repo_name):
		result = ["master"]
		repo_dir = self.zynthian_base_dir + "/" + repo_name

		check_output("cd {}; git remote update origin --prune".format(repo_dir), shell=True)
		for byteLine in check_output("cd {}; git branch -a".format(repo_dir), shell=True).splitlines():
			bname = byteLine.decode("utf-8").strip()
			if bname.startswith("*"):
				bname = bname[2:]
			if bname.startswith("remotes/origin/"):
				bname = bname[15:]
			if "->" in bname:
				continue
			if bname not in result:
				result.append(bname)

		return result

	def get_repo_current_branch(self, repo_name):
		repo_dir = self.zynthian_base_dir + "/" + repo_name

		for byteLine in check_output("cd {}; git branch | grep \* | cut -d ' ' -f2".format(repo_dir),
									 shell=True).splitlines():
			return byteLine.decode("utf-8")

	def set_repo_tag(self, repo_name, tag_name):
		logging.info("Changing repository '{}' to tag '{}'".format(repo_name, tag_name))

		repo_dir = self.zynthian_base_dir + "/" + repo_name
		current_branch = self.get_repo_current_branch(repo_name)

		if tag_name != current_branch:
			logging.info("... needs change: '{}' != '{}'".format(current_branch, tag_name))
			if tag_name == 'master':
				check_output("cd {}; git checkout .; git checkout {}".format(repo_dir, tag_name), shell=True)
			else:
				check_output(
					"cd {}; git checkout .; git branch -d {}; git checkout tags/{} -b {}".format(repo_dir, tag_name,
																								 tag_name, tag_name),
					shell=True)
			return True

	def set_repo_branch(self, repo_name, branch_name):
		logging.info("Changing repository '{}' to branch '{}'".format(repo_name, branch_name))

		repo_dir = self.zynthian_base_dir + "/" + repo_name
		current_branch = self.get_repo_current_branch(repo_name)

		if branch_name != current_branch:
			logging.info("... needs change: '{}' != '{}'".format(current_branch, branch_name))
			check_output("cd {}; git checkout .; git checkout {}".format(repo_dir, branch_name), shell=True)
			return True
