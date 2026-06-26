import base64
import hashlib
import os
import secrets
import urllib.parse
import netifaces
import requests
import logging
import argparse
import asyncio
import tornado.ioloop
import tornado.web

# === Configuration Constants ===
AUTHORIZE_URL = "https://www.tone3000.com/api/v1/oauth/authorize"
TOKEN_URL = "https://www.tone3000.com/api/v1/oauth/token"

# Default Zynthian Paths
ZYNTHIAN_MY_DATA_DIR = os.environ.get('ZYNTHIAN_MY_DATA_DIR', "/zynthian/zynthian-my-data")
DEFAULT_IR_DIR = f"{ZYNTHIAN_MY_DATA_DIR}/files/IRs"
DEFAULT_NAM_DIR = f"{ZYNTHIAN_MY_DATA_DIR}/files/Neural Models"

# === PKCE & State Generation ===
code_verifier = secrets.token_urlsafe(128)
code_challenge_hash = hashlib.sha256(code_verifier.encode("utf-8")).digest()
code_challenge = base64.urlsafe_b64encode(code_challenge_hash).decode("utf-8").rstrip("=")
state_token = secrets.token_urlsafe(32)

def get_interface_ip_from_iface(iface_name):
    try:
        iface = netifaces.ifaddresses(iface_name)
        if netifaces.AF_INET in iface:
            return iface[netifaces.AF_INET][0]['addr']
    except Exception as e:
        logging.debug(f"Interface {iface_name} not available: {e}")
    return None

# === Tornado Request Handler ===
class CallbackHandler(tornado.web.RequestHandler):
    async def get(self):
        # Parse URL parameters
        code = self.get_argument("code", None)
        state_param = self.get_argument("state", None)
        tone_id = self.get_argument("tone_id", None)
        canceled = self.get_argument("canceled", "false") == "true"

        # Access app settings
        app_settings = self.application.settings

        # Check State
        if state_param != app_settings.get("t3k_state"):
            self.set_status(400)
            self.write("State mismatch. Possible CSRF attack.")
            self.application.shutdown_server()
            return

        if canceled:
            print("User cancelled the flow.")
            self.write("<h1>Cancelled</h1><p>The user has cancelled the process.</p>")
            self.application.shutdown_server()
            return

        if not code:
            self.set_status(400)
            self.write("No authorization code received.")
            self.application.shutdown_server()
            return

        print(f"Code received: {code}")
        print(f"Tone-ID: {tone_id}")

        # === Token Exchange ===
        try:
            print("Sending token request to Tone3000...")
            token_response = requests.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": app_settings.get("client_id"),
                    "redirect_uri": app_settings.get("redirect_uri"),
                    "code": code,
                    "code_verifier": code_verifier,
                },
                timeout=10,
            )

            if token_response.status_code != 200:
                self.set_status(500)
                self.write(f"<h1>Token Exchange Error</h1><pre>{token_response.text}</pre>")
                self.application.shutdown_server()
                return

            access_token = token_response.json()["access_token"]
            print(f"Token successfully received: {access_token[:20]}...")

        except Exception as e:
            self.set_status(500)
            self.write(f"<h1>Error</h1><p>{e}</p>")
            self.application.shutdown_server()
            return

        # === Fetch Tone Metadata ===
        try:
            print("Fetching tone metadata...")
            tone_response = requests.get(
                f"https://www.tone3000.com/api/v1/tones/{tone_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )

            if tone_response.status_code != 200:
                self.set_status(500)
                self.write("<h1>Error</h1><p>Tone metadata not available</p>")
                self.application.shutdown_server()
                return

            tone_data = tone_response.json()
            is_ir_tone = (tone_data.get("gear") == "ir" or tone_data.get("platform") == "ir")
            
            a_models_count = [v for k, v in tone_data.items() if k.startswith("a") and k.endswith("_models_count")]
            tone_type = "IR" if (is_ir_tone and all(c == 0 for c in a_models_count)) else "NAM"
            print(f"Tone Type: {tone_type}")

        except Exception as e:
            self.set_status(500)
            self.write(f"<h1>Error</h1><p>Tone Metadata: {e}</p>")
            self.application.shutdown_server()
            return

        # === Determine Download Directory ===
        download_dir = app_settings.get("ir_dir") if tone_type == "IR" else app_settings.get("nam_dir")
        os.makedirs(download_dir, exist_ok=True)

        # === Fetch Models ===
        try:
            print("Fetching models...")
            models_response = requests.get(
                "https://www.tone3000.com/api/v1/models",
                params={"tone_id": tone_id},
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )

            if models_response.status_code != 200:
                self.set_status(500)
                self.write("<h1>Error</h1><p>Models not available</p>")
                self.application.shutdown_server()
                return

            models = models_response.json().get("data", [])
            if not isinstance(models, list):
                models = [models] if models else []

            print(f"{len(models)} models found.")

        except Exception as e:
            self.set_status(500)
            self.write(f"<h1>Error</h1><p>Models: {e}</p>")
            self.application.shutdown_server()
            return

        # === Download Models ===
        downloaded_files = []
        for model in models:
            model_url = model.get("model_url")
            if not model_url: continue

            model_name = model.get("name", "model.bin").replace("/", "_").replace("\\", "_")
            file_path = os.path.join(download_dir, model_name)
            try:
                print(f"Downloading: {model_name} -> {file_path}")
                res = requests.get(model_url, headers={"Authorization": f"Bearer {access_token}"}, stream=True, timeout=30)
                if res.status_code == 200:
                    with open(file_path, "wb") as f:
                        for chunk in res.iter_content(chunk_size=8192):
                            f.write(chunk)
                    downloaded_files.append(file_path)
                    print(f"Successfully downloaded: {file_path}")
            except Exception as e:
                print(f"Error downloading {model_name}: {e}")

        # === Response to Client ===
        html = f"""
        <h1 style="color: green;">Successfully downloaded!</h1>
        <p><strong>Tone Type:</strong> {tone_type}</p>
        <p><strong>Download Directory:</strong> {download_dir}</p>
        <p><strong>Downloaded Files:</strong></p>
        <ul>{"".join(f"<li>{f}</li>" for f in downloaded_files)}</ul>
        <hr>
        <p><a href="javascript:void(0)" onclick="window.close();">Close this window</a></p>
        """
        self.write(html)
        
        # Schedule shutdown after 1 second to ensure the browser receives the response
        asyncio.get_event_loop().call_later(1, self.application.shutdown_server)

# === Tornado Application Wrapper ===
class ToneApp(tornado.web.Application):
    def __init__(self, settings):
        super().__init__([ (r"/callback", CallbackHandler) ], **settings)

    def shutdown_server(self):
        print("Shutting down Tornado IOLoop...")
        # Correct way to stop the loop in modern Tornado/Asyncio
        tornado.ioloop.IOLoop.current().stop()

# === Main Execution ===
def start_server(client_id, port, interface, ir_dir, nam_dir):
    ip_addr = get_interface_ip_from_iface(interface)
    if not ip_addr:
        print(f"Error: Could not determine IP address for interface {interface}.")
        return
    
    redirect_uri = f"http://{ip_addr}:{port}/callback"

    # Prepare OAuth URL
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state_token,
        "prompt": "select_tone",
    }
    authorize_url = f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
    print(f"\nAuthorization URL:\n{authorize_url}\n")

    # Tornado Settings
    settings = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "t3k_state": state_token,
        "ir_dir": ir_dir,
        "nam_dir": nam_dir,
        "debug": False
    }

    app = ToneApp(settings)
    app.listen(port, address="0.0.0.0")

    print(f"Tornado server running on {ip_addr}:{port}")
    print("Waiting for callback... (open the browser if you are not logged in)")

    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nOAuth flow completed. Server stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tone3000 Model Downloader for Zynthian (Tornado)")
    parser.add_argument("--client_id", required=True, help="The OAuth Client ID")
    parser.add_argument("--port", type=int, default=63342, help="Local port (default: 63342)")
    parser.add_argument("--interface", type=str, default="eth0", help="Network interface (default: eth0)")
    parser.add_argument("--ir_dir", type=str, default=DEFAULT_IR_DIR, help=f"IR dir (default: {DEFAULT_IR_DIR})")
    parser.add_argument("--nam_dir", type=str, default=DEFAULT_NAM_DIR, help=f"NAM dir (default: {DEFAULT_NAM_DIR})")
    
    args = parser.parse_args()
    start_server(args.client_id, args.port, args.interface, args.ir_dir, args.nam_dir)
