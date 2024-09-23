# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Audio Configuration Handler
#
# Copyright (C) 2017-2024 Fernando Moyano <jofemodo@zynthian.org>
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
	stable_branch = os.environ.get('ZYNTHIAN_STABLE_BRANCH', "oram")
	stable_tag = os.environ.get('ZYNTHIAN_STABLE_TAG', "2409")
	testing_branch = os.environ.get('ZYNTHIAN_TESTING_BRANCH', "oram")

	repository_list = [
		['zynthian-ui', False],
		['zynthian-webconf', False],
		['zyncoder', True],
		['zynthian-sys', True],
		['zynthian-data', True]
	]

	@tornado.web.authenticated
	def get(self, errors=None):
		super().get("Repositories", self.get_config_info(), errors)

	@tornado.web.authenticated
	def post(self):
		postedConfig = tornado.escape.recursive_unicode(self.request.arguments)
		logging.info(postedConfig)
		try:
			version = postedConfig['ZYNTHIAN_VERSION'][0]
		except:
			version = self.stable_branch
		errors = {}
		changed_repos = 0
		for posted_config_key in postedConfig:
			if posted_config_key.startswith("ZYNTHIAN_REPO_"):
				repo_name = posted_config_key[len("ZYNTHIAN_REPO_"):]
				try:
					if version == "custom":
						branch = postedConfig[posted_config_key][0]
					else:
						branch = version
					if self.set_repo_branch(repo_name, branch):
						changed_repos += 1
				except Exception as err:
					logging.error(err)
					errors[f"ZYNTHIAN_REPO_{repo_name}"] = err

		config = self.get_config_info(version)
		if changed_repos > 0:
			config['ZYNTHIAN_MESSAGE'] = {
				'type': 'html',
				'content': "<div class='alert alert-success'>Some repo changed its branch. You may want to <a href='/sw-update'>update the software</a> for getting the latest changes.</div>"
			}
			#self.reboot_flag = True

		super().get("Repositories", config, errors)

	def get_config_info(self, version=None):
		stable_overall = True
		testing_overall = True
		repo_branches = []
		for repitem in self.repository_list:
			branch = self.get_repo_current_branch(repitem[0])
			stable_overall &= (branch == self.stable_branch)
			testing_overall &= (branch == self.testing_branch)
			repo_branches.append(branch)
		if version is None:
			if stable_overall:
				version = self.stable_branch
			elif testing_overall:
				version = self.testing_branch
			else:
				version = "custom"

		config = {
			"ZYNTHIAN_VERSION": {
				'type': 'select',
				'title': 'Version',
				'value': version,
				'options': [self.stable_branch, self.testing_branch, "custom"],
				'option_labels': {self.stable_branch: f"stable ({self.stable_branch})", self.testing_branch: f"testing ({self.testing_branch})", "custom": "custom"},
				'refresh_on_change': True,
				'advanced': False
			}
		}
		if version == "custom":
			for i, repitem in enumerate(self.repository_list):
				options = self.get_repo_branch_list(repitem[0])
				config[f"ZYNTHIAN_REPO_{repitem[0]}"] = {
					'type': 'select',
					'title': repitem[0],
					'value': repo_branches[i],
					'options': options,
					'option_labels': OrderedDict([(opt, opt) for opt in options]),
					'advanced': repitem[1]
				}
		config['_SPACER_'] = {
			'type': 'html',
			'content': "<br>"
		}
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
