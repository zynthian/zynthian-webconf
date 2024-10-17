# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Security Configuration Handler
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
import PAM
import logging
import tornado.web
from subprocess import check_output

from lib.zynthian_config_handler import ZynthianConfigHandler

# ------------------------------------------------------------------------------
# System Menu
# ------------------------------------------------------------------------------


class SecurityConfigHandler(ZynthianConfigHandler):

    @staticmethod
    def get_host_name():
        with open("/etc/hostname") as f:
            return f.readline()

    @tornado.web.authenticated
    def get(self, errors=None):
        # Get Hostname
        config = {
            'CURRENT_PASSWORD': {
                'type': 'password',
                'title': 'Current password',
                        'value': '*'
            },
            'PASSWORD': {
                'type': 'password',
                'title': 'Password',
                        'value': '*'
            },
            'REPEAT_PASSWORD': {
                'type': 'password',
                'title': 'Repeat password',
                        'value': '*'
            },
            'HOSTNAME': {
                'type': 'text',
                'title': 'Hostname',
                        'value': SecurityConfigHandler.get_host_name(),
                        'advanced': True
            },
            'REGENERATE_KEYS': {
                'type': 'button',
                'title': 'Regenerate Keys',
                        'script_file': 'regenerate_keys.js',
                        'button_type': 'button',
                        'class': 'btn-warning btn-block',
                        'advanced': True
            },
            '_command': {
                'type': 'hidden',
                'value': ''
            }
        }
        super().get("Security/Access", config, errors)

    @tornado.web.authenticated
    def post(self):
        params = tornado.escape.recursive_unicode(self.request.arguments)
        logging.debug(f"COMMAND: {params['_command'][0]}")
        if params['_command'][0] == "REGENERATE_KEYS":
            cmd = os.environ.get('ZYNTHIAN_SYS_DIR') + \
                "/sbin/regenerate_keys.sh"
            check_output(cmd, shell=True)
            self.redirect('/sys-reboot')
        else:
            errors = self.update_system_config(params)
            self.get(errors)

    def update_system_config(self, config):
        # PAM service callback
        def pam_conv(auth, query_list, userData):
            resp = []
            for i in range(len(query_list)):
                query, type = query_list[i]
                if type in (PAM.PAM_PROMPT_ECHO_ON, PAM.PAM_PROMPT_ECHO_OFF):
                    val = passwd
                    resp.append((val, 0))
                elif type == PAM.PAM_PROMPT_ERROR_MSG or type == PAM.PAM_PROMPT_TEXT_INFO:
                    logging.error(query)
                    resp.append(('', 0))
                else:
                    return None
            return resp

        # Check current password
        auth = PAM.pam()
        auth.start("passwd")
        auth.set_item(PAM.PAM_USER, "root")
        auth.set_item(PAM.PAM_CONV, pam_conv)
        try:
            passwd = self.get_argument("CURRENT_PASSWORD")
            auth.authenticate()
            auth.acct_mgmt()
        except PAM.error as resp:
            logging.info(f"Incorrect password => {resp}")
            return {"CURRENT_PASSWORD": "Incorrect Password"}
        except Exception as e:
            logging.error(e)
            return {"CURRENT_PASSWORD": "Authentication Failure"}

        # Change password
        if len(config['PASSWORD'][0]) > 0:
            if len(config['PASSWORD'][0]) < 6:
                return {'PASSWORD': "Password must have at least 6 characters"}
            if config['PASSWORD'][0] != config['REPEAT_PASSWORD'][0]:
                return {'REPEAT_PASSWORD': "Passwords does not match!"}

            # Change system password (PAM)
            try:
                passwd = config['PASSWORD'][0]
                auth.chauthtok()
                # auth.acct_mgmt()
            except PAM.error as resp:
                logging.error(f"Can't set new password! => {resp}")
                return {'REPEAT_PASSWORD': "Can't set new password for system!"}
            except Exception as e:
                logging.error(f"Can't set new password! => {e}")
                return {'REPEAT_PASSWORD': "Can't set new password for system!"}

            # Change VNC password
            try:
                check_output("echo \"{}\" | vncpasswd -f > /root/.vnc/passwd; chmod go-r /root/.vnc/passwd".format(
                    config['PASSWORD'][0]), shell=True)
            except Exception as e:
                logging.error(
                    "Can't set new password for VNC Server! => {}".format(e))
                return {'REPEAT_PASSWORD': "Can't set new password for VNC Server!"}

            # Change WIFI password
            try:
                check_output(
                    f"nmcli con modify zynthian-ap wifi-sec.psk \"{config['PASSWORD'][0]}\"", shell=True)
            except Exception as e:
                logging.error(
                    "Can't set new password for WIFI HotSpot! => {}".format(e))
                return {'REPEAT_PASSWORD': "Can't set new password for WIFI HotSpot!"}

        # Update Hostname
        newHostname = config['HOSTNAME'][0]

        try:
            with open("/etc/hostname", 'r') as f:
                previousHostname = f.readline()
                f.close()
        except:
            previousHostname = ''

        if previousHostname != newHostname:
            with open("/etc/hostname", 'w') as f:
                f.write(newHostname)
                f.close()

            with open("/etc/hosts", "r+") as f:
                contents = f.read()
                # contents = contents.replace(previousHostname, newHostname)
                contents = re.sub(r"127\.0\.1\.1.*$",
                                  "127.0.1.1\t{}".format(newHostname), contents)
                f.seek(0)
                f.truncate()
                f.write(contents)
                f.close()

            check_output(["hostnamectl", "set-hostname", newHostname])

            try:
                check_output(
                    f"nmcli con modify zynthian-ap wifi.ssid \"{newHostname}\"", shell=True)
            except Exception as e:
                logging.error("Can't set WIFI HotSpot name! => {}".format(e))
                return {'HOSTNAME': "Can't set WIFI HotSpot name!"}

            # self.reboot_flag=True
