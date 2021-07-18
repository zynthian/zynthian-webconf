# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# WIFI Configuration Handler
#
# Copyright (C) 2017 Markus Heidt <markus@heidt-tech.com>
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
import re
import sys
import logging
import base64
import tornado.web
from collections import OrderedDict

from lib.zynthian_config_handler import ZynthianBasicHandler

sys.path.append(os.environ.get('ZYNTHIAN_UI_DIR'))

# ------------------------------------------------------------------------------
# Wifi Config Handler
# ------------------------------------------------------------------------------


class WifiConfigHandler(ZynthianBasicHandler):

    wpa_supplicant_config_fpath = os.environ.get(
        'ZYNTHIAN_CONFIG_DIR', "/zynthian/config") + "/wpa_supplicant.conf"

    @tornado.web.authenticated
    def get(self, errors=None):

        idx = 0
        networks = []
        p = re.compile(
            '.*?network=\\{.*?ssid=\\"(.*?)\\".*?psk=\\"(.*?)\\"\n?(.*?)\\}.*?', re.I | re.M | re.S)
        iterator = p.finditer(self.read_wpa_supplicant_config())
        for m in iterator:
            networks.append({
                'idx': idx,
                'ssid': m.group(1),
                'ssid64': base64.b64encode(m.group(1).encode())[:5],
                'psk': m.group(2),
                'options': m.group(3)
            })
            idx += 1

        config = OrderedDict([
            ['ZYNTHIAN_WIFI_MODE', zynconf.get_current_wifi_mode()],
            ['ZYNTHIAN_WIFI_NETWORKS', networks]
        ])

        super().get("wifi.html", "Wifi", config, errors)

    @tornado.web.authenticated
    def post(self):
        errors = []

        try:
            action = self.get_argument('ZYNTHIAN_WIFI_ACTION')
            logging.debug("ACTION: {}".format(action))
        except:
            action = "SET_MODE"

        try:
            if action == "ADD_NETWORK":
                newSSID = self.get_argument('ZYNTHIAN_WIFI_NEW_SSID')
                newPassword = self.get_argument('ZYNTHIAN_WIFI_NEW_PASSWORD')
                if newSSID and newPassword:
                    self.add_new_network(newSSID, newPassword)

            elif action[:7] == "REMOVE_":
                delSSID = action[7:]
                self.remove_network(delSSID)

            elif action[:7] == "UPDATE_":
                updSSID = action[7:]
                updOptions = self.get_argument(
                    'ZYNTHIAN_WIFI_OPTIONS_{}'.format(updSSID))
                self.update_network_options(updSSID, updOptions)

            elif action == "SET_MODE":
                wifi_mode = self.get_argument('ZYNTHIAN_WIFI_MODE')
                current_wifi_mode = zynconf.get_current_wifi_mode()
                if wifi_mode != current_wifi_mode:

                    if wifi_mode == "on":
                        if not zynconf.start_wifi():
                            errors.append("Can't start WIFI network!")

                    elif wifi_mode == "hotspot":
                        if not zynconf.start_wifi_hotspot():
                            errors.append("Can't start WIFI Hotspot!")

                    else:
                        if not zynconf.stop_wifi():
                            errors.append("Can't stop WIFI!")

        except Exception as e:
            errors.append(e)

        self.get(errors)

    def read_wpa_supplicant_config(self):
        try:
            fo = open(self.wpa_supplicant_config_fpath, "r")
            wpa_supplicant_config = "".join(fo.readlines())
            fo.close()
            return wpa_supplicant_config

        except Exception as e:
            logging.error(
                "Can't read WIFI network configuration: {}".format(e))
            return ""

    def save_wpa_supplicant_config(self, data):
        try:
            fo = open(self.wpa_supplicant_config_fpath, "w")
            fo.write(data)
            fo.flush()
            fo.close()

        except Exception as e:
            logging.error(
                "Can't save WIFI network configuration: {}".format(e))

    def add_new_network(self, newSSID, newPassword):
        logging.info("Add Network: {}".format(newSSID))
        wpa_supplicant_data = self.read_wpa_supplicant_config()
        wpa_supplicant_data += '\nnetwork={\n'
        wpa_supplicant_data += '\tssid="{}"\n'.format(newSSID)
        wpa_supplicant_data += '\tpsk="{}"\n'.format(newPassword)
        wpa_supplicant_data += '\tscan_ssid=1\n'
        wpa_supplicant_data += '\tkey_mgmt=WPA-PSK\n'
        wpa_supplicant_data += '\tpriority=10\n'
        wpa_supplicant_data += '}\n'
        self.save_wpa_supplicant_config(wpa_supplicant_data)

    def remove_network(self, delSSID):
        logging.info("Remove Network: {}".format(delSSID))

        wpa_supplicant_data = self.read_wpa_supplicant_config()

        i = wpa_supplicant_data.find("network={")
        wpa_supplicant_header = wpa_supplicant_data[:i]

        p = re.compile(
            '.*?network=\\{.*?ssid=\\"(.*?)\\".*?psk=\\"(.*?)\\"\n?(.*?)\\}.*?', re.I | re.M | re.S)
        iterator = p.finditer(wpa_supplicant_data[i:])

        for m in iterator:
            if m.group(1) != delSSID:
                wpa_supplicant_header += m.group(0)

        self.save_wpa_supplicant_config(wpa_supplicant_header)

    def update_network_options(self, updSSID, options):
        logging.info("Update Network Options: {}".format(updSSID))

        wpa_supplicant_data = self.read_wpa_supplicant_config()

        i = wpa_supplicant_data.find("network={")
        wpa_supplicant_header = wpa_supplicant_data[:i]

        p = re.compile(
            '.*?network=\\{.*?ssid=\\"(.*?)\\".*?psk=\\"(.*?)\\"\n?(.*?)\\}.*?', re.I | re.M | re.S)
        iterator = p.finditer(wpa_supplicant_data[i:])

        for m in iterator:
            if m.group(1) != updSSID:
                wpa_supplicant_header += m.group(0)
            else:
                wpa_supplicant_header += '\nnetwork={\n'
                wpa_supplicant_header += '\tssid="{}"\n'.format(m.group(1))
                wpa_supplicant_header += '\tpsk="{}"\n'.format(m.group(2))
                wpa_supplicant_header += '\t{}\n'.format(options)
                wpa_supplicant_header += '}\n'

        self.save_wpa_supplicant_config(wpa_supplicant_header)
