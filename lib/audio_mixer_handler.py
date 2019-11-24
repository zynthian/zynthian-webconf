# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Audio Mixer Handler
#
# Copyright (C) 2019 Fernando Moyano <jofemodo@zynthian.org>
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
from subprocess import check_output

#------------------------------------------------------------------------------
# Audio Configuration
#------------------------------------------------------------------------------

class AudioMixerHandler(tornado.web.RequestHandler):

	def initialize(self):
		self.device_name = self.get_device_name()


	def get_current_user(self):
		return self.get_secure_cookie("user")


	@tornado.web.authenticated
	def post(self, ctrl, val):
		result = {}

		if ctrl.find('Playback')>=0:
			channelType = 'Playback'
			mixerControl = ctrl[9:].replace('_',' ')
		elif ctrl.find('Capture')>=0:
			channelType = 'Capture'
			mixerControl = ctrl[8:].replace('_',' ')
		else:
			return

		try:
			amixer_command = "amixer -M -c {} set '{}' {} {}% unmute".format(self.device_name, mixerControl, channelType, val)
			logging.debug(amixer_command)
			check_output(amixer_command, shell=True)

		except Exception as err:
			result['errors'] = str(err)
			logging.error(err)

		# JSON Ouput
		if result:
			self.write(result)


	def get_device_name(self):
		try:
			jack_opts=os.environ.get('JACKD_OPTIONS')
			res = re.compile(r" hw:([^\s]+) ").search(jack_opts)
			return res.group(1)
		except:
			return "0"

