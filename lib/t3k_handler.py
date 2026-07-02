# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Tone3000 config handler
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
import logging
import requests
import argparse
import tornado.web
import urllib.parse

import zynconf
from lib.zynthian_config_handler import ZynthianBasicHandler

import lib.t3k_auth


# === Configuration constants ===

T3K_API_URLBASE = "https://www.tone3000.com/api/v1"
T3K_API_KEY = os.environ.get("ZYNTHIAN_T3K_API_KEY", "")
AUTHORIZE_URL = f"{T3K_API_URLBASE}/oauth/authorize"
TOKEN_URL = f"{T3K_API_URLBASE}/oauth/token"

class T3kConfigHandler(ZynthianBasicHandler):

        def get_redirect_uri(self):
            return f"https://{self.request.host}/lib-t3k-download"

        @tornado.web.authenticated
        def get(self, errors=None):
            config = {
                'ZYNTHIAN_T3K_API_KEY': T3K_API_KEY,
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
                except Exceptions as e:
                    logging.error(f"Cannot start local server: {e}")
                    error="Cannot start local server."
            self.get(error)

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

        def get_authorize_url(self):
            params = {
                "client_id": T3K_API_KEY,
                "redirect_uri": self.get_redirect_uri(),
                "response_type": "code",
                "code_challenge": lib.t3k_auth.code_challenge,
                "code_challenge_method": "S256",
                "state": lib.t3k_auth.state_token,
                "prompt": "select_tone",
            }
            query_string = urllib.parse.urlencode(params)
            authorize_url = f"{AUTHORIZE_URL}?{query_string}"
            return authorize_url


class T3kDownloadHandler(ZynthianBasicHandler):

    # Zynthian paths
    ZYNTHIAN_MY_DATA_DIR = os.environ.get('ZYNTHIAN_MY_DATA_DIR', "/zynthian/zynthian-my-data")
    ZYNTHIAN_IR_DIR = f"{ZYNTHIAN_MY_DATA_DIR}/files/IRs"
    ZYNTHIAN_NAM_DIR = f"{ZYNTHIAN_MY_DATA_DIR}/files/Neural Models"


    def get_redirect_uri(self):
        return f"https://{self.request.host}/lib-t3k-download"

    @tornado.web.authenticated
    def get(self):
        code = self.get_argument("code", None)
        state_param = self.get_argument("state", None)
        tone_id = self.get_argument("tone_id", None)
        canceled = self.get_argument("canceled", "false") == "true"

        app_settings = self.application.settings

        if state_param != lib.t3k_auth.state_token:
            self.set_status(400)
            self.write("State mismatch. Possible CSRF attack.")
            return

        if canceled:
            logging.debug(f"User cancelled the flow.")
            self.write("<h1>Cancelled</h1><p>The user has cancelled the process.</p>")
            return

        if not code:
            self.set_status(400)
            self.write("No authorization code received.")
            return

        logging.debug(f"Code received: {code}\nTone-ID: {tone_id}")

        try:
            logging.debug(f"Sending token request to Tone3000...")
            token_response = requests.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": T3K_API_KEY,
                    "redirect_uri": self.get_redirect_uri(),
                    "code": code,
                    "code_verifier": lib.t3k_auth.code_verifier,
                },
                timeout=10,
            )

            if token_response.status_code != 200:
                self.set_status(500)
                self.write(f"<h1>Token Exchange Error</h1><pre>{token_response.text}</pre>")
                return

            access_token = token_response.json()["access_token"]
            logging.debug(f"Token successfully received: {access_token[:20]}...")
        except Exception as e:
            self.set_status(500)
            self.write(f"<h1>Error</h1><p>{e}</p>")
            return

        try:
            logging.debug(f"Fetching tone metadata...")

            tone_response = requests.get(
                f"{T3K_API_URLBASE}/tones/{tone_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )

            tone_response = requests.get(
                f"{T3K_API_URLBASE}/tones/{tone_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )

            logging.debug(f"Tone Response Status Code => {tone_response.status_code}")
            if tone_response.status_code != 200:
                self.set_status(500)
                self.write("<h1>Error</h1><p>Tone metadata not available</p>")
                return

            tone_data = tone_response.json()
            logging.debug(f"Tone Data => {tone_data=}")

            is_ir_tone = (tone_data.get("format") == "ir")
            a_models_count = [v for k, v in tone_data.items() if k.startswith("a") and k.endswith("_models_count")]
            
            if is_ir_tone and all(c == 0 for c in a_models_count):
                tone_type = "IR"
            else:
                tone_type = "NAM"
            
            logging.debug(f"Detected Tone Type: {tone_type}")

        except Exception as e:
            self.set_status(500)
            self.write(f"<h1>Error</h1><p>Tone Metadata: {e}</p>")
            return

        if tone_type == "IR":
            download_dir = self.ZYNTHIAN_IR_DIR
        else:
            download_dir = self.ZYNTHIAN_NAM_DIR

        if tone_data['title']:
            download_dir = download_dir + "/" + tone_data['title']
        os.makedirs(download_dir, exist_ok=True)

        try:
            logging.debug(f"Fetching models...")
            models_response = requests.get(f"{T3K_API_URLBASE}/models",
                params={"tone_id": tone_id},
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )

            if models_response.status_code != 200:
                self.set_status(500)
                self.write("<h1>Error</h1><p>Models not available</p>")
                return

            models = models_response.json().get("data", [])
            if not isinstance(models, list):
                models = [models] if models else []

            logging.debug(f"{len(models)} models found.")

        except Exception as e:
            self.set_status(500)
            self.write(f"<h1>Error</h1><p>Models: {e}</p>")
            return

        self.write("""
            <link rel="stylesheet" href="/css/fonts.css">
            <link rel="stylesheet" href="/css/style.css">
            <link rel="stylesheet" href="/css/default.css">
            <link rel="stylesheet" href="/css/zynthian.css">
        """)

        downloaded_files = []
        for model in models:
            model_url = model.get("model_url")
            if not model_url: continue

            model_name = model.get("name", "model.bin").replace("/", "_").replace("\\", "_")
            if model_name[-4:].lower() != ".nam":
                model_name += ".nam"
            file_path = os.path.join(download_dir, model_name)
            try:
                logging.debug(f"Downloading: {model_name} -> {file_path}")
                res = requests.get(model_url, headers={"Authorization": f"Bearer {access_token}"}, stream=True, timeout=30)
                if res.status_code == 200:
                    with open(file_path, "wb") as f:
                        for chunk in res.iter_content(chunk_size=8192):
                            f.write(chunk)
                    downloaded_files.append(file_path)
                    logging.debug(f"Successfully downloaded: {file_path}")
            except Exception as e:
                logging.debug(f"Error downloading {model_name}: {e}")

        html = f"""
        <h1 style="color: green;">Successfully downloaded!</h1>
        <p><strong>Tone Type:</strong> {tone_type}</p>
        <p><strong>Saved to:</strong> {download_dir}</p>
        <p><strong>Downloaded Files:</strong></p>
        <ul>{"".join(f"<li>{f}</li>" for f in downloaded_files)}</ul>
        <hr>
        <p><a href="javascript:void(0)" onclick="window.close();">Close this window</a></p>
        """
        self.write(html)
