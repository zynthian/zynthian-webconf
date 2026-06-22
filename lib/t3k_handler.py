# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Tone3000 Config Handler
#
# Copyright (C) 2026 Holger Wirtz <holger@zynthian.org>
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
import sys
import psutil
import shutil
import logging
import tornado.web

import zynconf
from lib.zynthian_config_handler import ZynthianBasicHandler

# ------------------------------------------------------------------------------
# Tone 3000 Configuration
# ------------------------------------------------------------------------------

class T3kHandler(ZynthianBasicHandler):
    #zynthian_my_data_dir = os.environ.get('ZYNTHIAN_MY_DATA_DIR', "/zynthian/zynthian-my-data")
    #ir_dir = f"{zynthian_my_data_dir}/files/IRs"
    #nam_dir = f"{zynthian_my_data_dir}/files/Neural Models"

    @tornado.web.authenticated
    def get(self, errors=None):
        config = {
            'ZYNTHIAN_T3K_API_KEY': self.get_t3k_api_key()
        }
        if errors:
            logging.error("T3k Action Failed: %s" % format(errors))
        super().get("t3k.html", "Tone 3000", config, errors)

    @tornado.web.authenticated
    def post(self):
        error = None
        try:
            action = self.get_argument('ZYNTHIAN_T3K_API_KEY_ACTION')
        except:
            action = None
            logging.error(f"No action!")

        if action == "STORE_T3K_API_KEY":
            t3k_api_key = self.get_argument('ZYNTHIAN_T3K_API_KEY')
            error = self.do_save_config()
            logging.error(f"{error}")
        self.get(error)

    def get_t3k_api_key(self):
        return(os.environ.get('ZYNTHIAN_T3K_API_KEY'))

    def do_save_config(self):
        error = None
        config = {
            "ZYNTHIAN_T3K_API_KEY": self.get_argument('ZYNTHIAN_T3K_API_KEY'),
        }
        try:
            error = zynconf.save_config(config, updsys=True)
        except Exceptions as e:
            error = "Cannot store Tone 3000 API key."
        return(error)

# *****************************************************************************
