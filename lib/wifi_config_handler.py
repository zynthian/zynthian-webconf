# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# WIFI Configuration Handler
#
# Copyright (C) 2017-2024 Markus Heidt <markus@heidt-tech.com>
#                         Fernando Moyano <fernando@zynthian.org>
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

import zynconf
import os
import sys
import logging
import tornado.web

from lib.zynthian_config_handler import ZynthianBasicHandler

sys.path.append(os.environ.get('ZYNTHIAN_UI_DIR'))

# ------------------------------------------------------------------------------
# Wifi Config Handler
# ------------------------------------------------------------------------------


class WifiConfigHandler(ZynthianBasicHandler):

    @tornado.web.authenticated
    def get(self, errors=None):
        networks = []
        for wifi in zynconf.get_wifi_list():
            networks.append({
                'ssid': wifi[0],
                'description': wifi[2],
                'configured': wifi[3],
                'enabled': wifi[4]
            })
        config = {
            'ZYNTHIAN_WIFI_STATUS': zynconf.get_nwdev_status_code("wlan0"),
            'ZYNTHIAN_WIFI_NETWORKS': networks
        }
        if 'X-Requested-With' in self.request.headers and self.request.headers['X-Requested-With'] == 'XMLHttpRequest':
            self.write(config)
        else:
            super().get("wifi.html", "Wifi", config, errors)

    @tornado.web.authenticated
    def post(self):
        errors = []

        try:
            action = self.get_argument('ZYNTHIAN_WIFI_ACTION')
            logging.debug("ACTION: {}".format(action))
        except:
            action = ""

        try:
            if action == "ENABLE_WIFI":
                pass
            elif action == "DISABLE_WIFI":
                pass
            elif action == "ENABLE_NETWORK":
                ssid = self.get_argument('ZYNTHIAN_WIFI_ACTION_SSID')
                pass
            elif action == "DISABLE_NETWORK":
                ssid = self.get_argument('ZYNTHIAN_WIFI_ACTION_SSID')
                pass
        except Exception as e:
            errors.append(e)

        self.get(errors)
