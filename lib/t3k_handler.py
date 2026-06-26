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
import logging
import tornado.web
import base64
import hashlib
import secrets
import socket
import netifaces
import urllib.parse

import zynconf
from lib.zynthian_config_handler import ZynthianBasicHandler

# ------------------------------------------------------------------------------
# Tone 3000 configuration
# ------------------------------------------------------------------------------

class T3kHandler(ZynthianBasicHandler):
    @tornado.web.authenticated
    def get(self, errors=None):
        config = {
            'ZYNTHIAN_T3K_API_KEY': self.get_t3k_api_key(),
            'ZYNTHIAN_T3K_URL': self.get_authorize_url()
        }
        if errors:
            logging.error("T3k Action Failed: %s" % format(errors))
        super().get("t3k.html", "Tone 3000", config, errors)

    @tornado.web.authenticated
    def post(self):
        error = None
        try:
            action = self.get_argument('ZYNTHIAN_T3K_ACTION')
        except:
            action = None
            logging.error(f"No action!")

        if action == "STORE_T3K_API_KEY":
            t3k_api_key = self.get_argument('ZYNTHIAN_T3K_API_KEY')
            error = self.do_save_config()
            if error:
                logging.error(f"{error}")
        elif action == "GO_TO_T3K":
            authorize_url = self.get_authorize_url()
            try:    
                self.set_header("Content-Type", "text/html; charset=UTF-8")
                self.write(f"""
                <html>
                <head>
                    <title>Tone 3000</title>
                    <script>
                        window.onload = function() {{
                            window.open("{authorize_url}", "_blank");
                        }};
                    </script>
                </head>
                <body>
                    <p>One moment...</p>
                </body>
                </html>
                """)
                print(f"{authorize_url=}")
            except Exceptions as e:
                logging.error(f"Cannot start local server: {e}")
                error="Cannot start local server."
        self.get(error)

    def get_t3k_api_key(self):
        return(os.environ.get('ZYNTHIAN_T3K_API_KEY'))
    
    def get_interface_ip(self):
        interfaces = ['eth0', 'wlan0']
        
        for iface in interfaces:
            ip = self.get_interface_ip_from_iface(iface)  # ✅ Mit self.
            if ip and (ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.')):
                logging.debug(f"IP found {iface}: {ip}")
                return ip

        logging.error("No local IP found.")
        return None

    def get_interface_ip_from_iface(self, iface_name):
        try:
            iface = netifaces.ifaddresses(iface_name)
            if netifaces.AF_INET in iface:
                ip = iface[netifaces.AF_INET][0]['addr']
                return ip
        except Exception as e:
            logging.debug(f"Interface {iface_name} not available: {e}")
        return None

    def get_authorize_url(self):
        REDIRECT_URI = f"http://{self.get_interface_ip()}/lib-t3k"
        AUTHORIZE_URL = "https://www.tone3000.com/api/v1/oauth/authorize"

        authorize_url = None
        state = None
        try:
            code_verifier = secrets.token_urlsafe(128)
            code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
            code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8").rstrip("=")
            state = secrets.token_urlsafe(32)
            print(f"1:{state=}")
            
            params = {
                "client_id": self.get_t3k_api_key(),
                "redirect_uri": REDIRECT_URI,
                "response_type": "code",
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "state": state,
                "prompt": "select_tone",
            }

            self.set_secure_cookie(
                "t3k_state",
                state,
                expires_days=1
            )
            print(f"2:{self.get_secure_cookie('t3k_state')}")

            query_string = urllib.parse.urlencode(params)
            authorize_url = f"{AUTHORIZE_URL}?{query_string}"
        except Exception as e:
            logging.error(f"{e}")
            print(f"{e}")

        return authorize_url

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
