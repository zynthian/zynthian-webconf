# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Poweroff Handler
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

import logging
import tornado.web
from os import system

from lib.zynthian_config_handler import ZynthianBasicHandler

# ------------------------------------------------------------------------------
# Poweroff Handler
# ------------------------------------------------------------------------------


class PoweroffHandler(ZynthianBasicHandler):

    @tornado.web.authenticated
    def get(self):
        self.reboot_flag = False
        super().get("poweroff_confirm_block.html", "Power Off", None, None)

    @tornado.web.authenticated
    def post(self):
        if self.genjson:
            self.write("POWEROFF")
        else:
            self.render("config.html", body="poweroff_block.html",
                        config=None, title="Power Off", errors=None)
        try:
            system("killall -SIGQUIT zynthian_gui.py; sleep 4; poweroff")
        except Exception as e:
            logging.error(e)
