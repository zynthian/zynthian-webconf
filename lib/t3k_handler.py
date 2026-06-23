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
# Tone 3000 configuration
# ------------------------------------------------------------------------------

class T3kHandler(ZynthianBasicHandler):
    REDIRECT_URI = "http://localhost:8000/callback"
    AUTHORIZE_URL = "https://www.tone3000.com/api/v1/oauth/authorize"
    TOKEN_URL = "https://www.tone3000.com/api/v1/oauth/token"

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
            state,authorize_url = self.get_authorize_url()    
            self.start_local_server(state)
            self.set_header("Content-Type", "text/html; charset=UTF-8")
            self.write(f"""
            <html>
            <head>
                <title>Tone 3000</title>
                <script>
                    window.onload = function() {
                        window.open("{config['ZYNTHIAN_T3K_URL']}", "_blank");
                    };
                </script>
            </head>
            <body>
                <p>One moment...</p>
            </body>
            </html>
            """)
        self.get(error)

    def get_t3k_api_key(self):
        return(os.environ.get('ZYNTHIAN_T3K_API_KEY'))
    
    def get_authorize_url(self):
        authorize_url = None
        try:
            code_verifier = secrets.token_urlsafe(128)
            
            code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
            code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8").rstrip("=")

            params = {
                "client_id": self.get_t3k_api_key(),
                "redirect_uri": REDIRECT_URI,
                "response_type": "code",
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "state": state,
                "prompt": "select_tone",
            }

            query_string = urllib.parse.urlencode(params)
            authorize_url = f"{AUTHORIZE_URL}?{query_string}"
        except Exception as e:
            logging.error(f"{e}")
            
        return state,authorize_url

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

    def start_local_server(state):
        PORT = 8000

        with socketserver.TCPServer(("", PORT), WebServerCallbackHandler) as httpd:
            httpd.session = {"t3k_state": state}
            httpd.shutdown_event = threading.Event()

            server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            server_thread.start()
            logging.info(f"Local callback server started at http://localhost:{PORT}")

            # wait for callback
            httpd.shutdown_event.wait()
            httpd.shutdown()
            httpd.server_close()
            logging.info(f"Local callback server started at http://localhost:{PORT}")

# Local webserver callback
class WebServerCallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        zynthian_my_data_dir = os.environ.get('ZYNTHIAN_MY_DATA_DIR', "/zynthian/zynthian-my-data")
        ir_dir = f"{zynthian_my_data_dir}/files/IRs"
        nam_dir = f"{zynthian_my_data_dir}/files/Neural Models"
        
        # Parse URL
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        code = query_params.get("code", [None])[0]
        state = query_params.get("state", [None])[0]
        tone_id = query_params.get("tone_id", [None])[0]
        canceled = query_params.get("canceled", [None])[0] == "true"

        # Check state
        if state != self.server.session.get("t3k_state"):
            logging.error("State mismatch. Possible CSRF attack.")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"State mismatch. Possible CSRF attack.")
            self.server.shutdown_event.set()
            return

        if canceled:
            logging.error("User has cancelled flow.")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(
                b"<h1>Canceled</h1><p>"
            )
            self.server.shutdown_event.set()
            return

        if not code:
            logging.error("No code.")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No code.")
            self.server.shutdown_event.set()
            return

        logging.info(f"Got code: {code}\nTone-ID: {tone_id}")

        # === Token exchange ===
        try:
            logging.info("Sending token to T3k:")
            logging.info(f"client_id: {CLIENT_ID}")
            logging.info(f"  - redirect_uri: {REDIRECT_URI}")
            logging.info(f"  - code: {code}")
            logging.info(f"  - code_verifier: {code_verifier[:10]}...")

            token_response = requests.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": CLIENT_ID,
                    "redirect_uri": REDIRECT_URI,
                    "code": code,
                    "code_verifier": code_verifier,
                },
                timeout=10,
            )

            logging.info(f"Response state: {token_response.status_code}")
            logging.info(f"Response body: {token_response.text}")

            if token_response.status_code != 200:
                logging.error("Token exchange failed!")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(
                    f"<h1>Token exchange error</h1><p>State: {token_response.status_code}</p><pre>{token_response.text}</pre>".encode()
                )
                self.server.shutdown_event.set()
                return

            token_data = token_response.json()
            access_token = token_data["access_token"]
            logging.info(f"Got token: {access_token[:20]}...")

        except Exception as e:
            logging.error(f"Token exchange exception: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"<h1>Error</h1><p>{e}</p>".encode())
            self.server.shutdown_event.set()
            return

        # === Get tone data ===
        try:
            logging.info("Loading tone meta data...")
            tone_response = requests.get(
                f"https://www.tone3000.com/api/v1/tones/{tone_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            logging.info(f"Tone state: {tone_response.status_code}")
            logging.info(f"Tone body: {tone_response.text}")

            if tone_response.status_code != 200:
                logging.error("Error while retrieving tone meta data.")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(
                    f"<h1>Error</h1><p>Tone meta data is not available</p><pre>{tone_response.text}</pre>".encode()
                )
                self.server.shutdown_event.set()
                return

            tone_data = tone_response.json()
            # check if it is an IR
            is_ir_tone = (
                tone_data.get("gear") == "ir" or tone_data.get("platform") == "ir"
            )

            # get all aX_models_count values
            a_models_count = [
                value
                for key, value in tone_data.items()
                if key.startswith("a") and key.endswith("_models_count")
            ]

            # If all are 0 and if it is an IR, set tone_name to "IR"
            if is_ir_tone and all(count == 0 for count in a_models_count):
                download_dir = ir_dir
            else:
                download_dir = nam_dir

            logging.info(f"Tone type: {tone_name}")

        except Exception as e:
            logging.error(f"Tone meta data exception: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"<h1>Error</h1><p>Tone meta data: {e}</p>".encode())
            self.server.shutdown_event.set()
            return

        # === Get modells ===
        try:
            logging.info("Loading model list...")
            models_response = requests.get(
                "https://www.tone3000.com/api/v1/models",
                params={"tone_id": tone_id},
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            logging.info(f"Model state: {models_response.status_code}")
            logging.info(f"Model body: {models_response.text}")

            if models_response.status_code != 200:
                logging.error("Error while retreaving models.")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(
                    f"<h1>Error</h1><p>Models not available</p><pre>{models_response.text}</pre>".encode()
                )
                self.server.shutdown_event.set()
                return

            models_data = models_response.json()
            logging.info(f"models (JSON): {models_data}")

            # Extrahiere die Liste der Modelle
            models = models_data.get("data", [])
            if not isinstance(models, list):
                logging.warn(
                    "model data is not a list"
                )
                models = models

            logging.info(f"Found {len(models)} models.")

        except Exception as e:
            logging.info(f"Error while retreaving models: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"<h1>Error</h1><p>Models: {e}</p>".encode())
            self.server.shutdown_event.set()
            return

        # === Model download ===
        os.makedirs(download_dir, exist_ok=True)

        downloaded_files = []
        for model in models:
            model_url = model.get("model_url")
            if not model_url:
                logging.info("No model_url for model, skipping...")
                continue

            model_name = (
                model.get("name", "model.bin").replace("/", "_").replace("\\", "_")
            )
            file_path = os.path.join(download_dir, model_name)
            try:
                logging.info(f"Download: {model_name} -> {file_path}")

                download_response = requests.get(
                    model_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                    stream=True,
                    timeout=30,
                )
                if download_response.status_code != 200:
                    logging.error(f"Download error: {download_response.status_code} / {download_response.text}")
                    continue

                with open(file_path, "wb") as f:
                    for chunk in download_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                downloaded_files.append(file_path)
                logging.info(f"Successfully downloaded: {file_path}")

            except Exception as e:
                logging.error(f"Error while downloading {model_name}: {e}")

        # === Answer to the client ===
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = f"""
        <h1>Successfully downloaded</h1>
        <p><strong>Tone:</strong> {tone_name}</p>
        <p><strong>Download directory:</strong> {download_dir}</p>
        <p><strong>Files downloaded:</strong></p>
        <ul>
        {"".join(f"<li>{f}</li>" for f in downloaded_files)}
        </ul>
        <p><a href="/">Back</a></p>
        """
        self.wfile.write(html.encode())

        # === Server beenden ===
        self.server.shutdown_event.set()

# *****************************************************************************
