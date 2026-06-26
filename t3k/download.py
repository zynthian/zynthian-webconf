import base64
import hashlib
import http.server
import os
import secrets
import socketserver
import threading
import urllib
import netifaces
import requests
import logging
import argparse

def get_interface_ip_from_iface(iface_name):
    try:
        iface = netifaces.ifaddresses(iface_name)
        if netifaces.AF_INET in iface:
            ip = iface[netifaces.AF_INET][0]['addr']
            return ip
    except Exception as e:
        logging.debug(f"Interface {iface_name} not available: {e}")
    return None

# === Configuration Constants ===
AUTHORIZE_URL = "https://www.tone3000.com/api/v1/oauth/authorize"
TOKEN_URL = "https://www.tone3000.com/api/v1/oauth/token"

# Default Zynthian Paths
ZYNTHIAN_MY_DATA_DIR = os.environ.get('ZYNTHIAN_MY_DATA_DIR', "/zynthian/zynthian-my-data")
DEFAULT_IR_DIR = f"{ZYNTHIAN_MY_DATA_DIR}/files/IRs"
DEFAULT_NAM_DIR = f"{ZYNTHIAN_MY_DATA_DIR}/files/Neural Models"

# === 1. PKCE: Generate Code Verifier ===
code_verifier = secrets.token_urlsafe(128)

# === 2. Code Challenge (S256) ===
code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8").rstrip("=")

# === 3. Generate State ===
state = secrets.token_urlsafe(32)

# === Local Webserver for Callback ===
class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse URL
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        code = query_params.get("code", [None])[0]
        state_param = query_params.get("state", [None])[0]
        tone_id = query_params.get("tone_id", [None])[0]
        canceled = query_params.get("canceled", [None])[0] == "true"

        # Check State
        if state_param != self.server.session.get("t3k_state"):
            print("State mismatch. Possible CSRF attack.")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"State mismatch. Possible CSRF attack.")
            self.server.shutdown_event.set()
            return

        if canceled:
            print("User cancelled the flow.")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(
                b"<h1>Cancelled</h1><p>The user has cancelled the process.</p>"
            )
            self.server.shutdown_event.set()
            return

        if not code:
            print("No authorization code received.")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No authorization code received.")
            self.server.shutdown_event.set()
            return

        print(f"Code received: {code}")
        print(f"Tone-ID: {tone_id}")

        # === Token Exchange ===
        try:
            client_id = self.server.session.get("client_id")
            redirect_uri = self.server.session.get("redirect_uri")

            print("Sending token request to Tone3000...")
            token_response = requests.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "redirect_uri": redirect_uri,
                    "code": code,
                    "code_verifier": code_verifier,
                },
                timeout=10,
            )

            if token_response.status_code != 200:
                print("Token exchange failed!")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(
                    f"<h1>Token Exchange Error</h1><p>Status: {token_response.status_code}</p><pre>{token_response.text}</pre>".encode()
                )
                self.server.shutdown_event.set()
                return

            token_data = token_response.json()
            access_token = token_data["access_token"]
            print(f"Token successfully received: {access_token[:20]}...")

        except Exception as e:
            print(f"Exception during token exchange: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"<h1>Error</h1><p>{e}</p>".encode())
            self.server.shutdown_event.set()
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
                print("Error fetching tone metadata.")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(
                    f"<h1>Error</h1><p>Tone metadata not available</p><pre>{tone_response.text}</pre>".encode()
                )
                self.server.shutdown_event.set()
                return

            tone_data = tone_response.json()
            is_ir_tone = (
                tone_data.get("gear") == "ir" or tone_data.get("platform") == "ir"
            )

            a_models_count = [
                value
                for key, value in tone_data.items()
                if key.startswith("a") and key.endswith("_models_count")
            ]

            if is_ir_tone and all(count == 0 for count in a_models_count):
                tone_type = "IR"
            else:
                tone_type = "NAM"

            print(f"Tone Type: {tone_type}")

        except Exception as e:
            print(f"Error fetching tone metadata: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"<h1>Error</h1><p>Tone Metadata: {e}</p>".encode())
            self.server.shutdown_event.set()
            return

        # === Determine Download Directory ===
        if tone_type == "IR":
            download_dir = self.server.session.get("ir_dir")
        else:
            download_dir = self.server.session.get("nam_dir")
        
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
                print("Error fetching models.")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(
                    f"<h1>Error</h1><p>Models not available</p><pre>{models_response.text}</pre>".encode()
                )
                self.server.shutdown_event.set()
                return

            models_data = models_response.json()
            models = models_data.get("data", [])
            if not isinstance(models, list):
                models = models

            print(f"{len(models)} models found.")

        except Exception as e:
            print(f"Error fetching models: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"<h1>Error</h1><p>Models: {e}</p>".encode())
            self.server.shutdown_event.set()
            return

        # === Download Models ===
        downloaded_files = []
        for model in models:
            model_url = model.get("model_url")
            if not model_url:
                continue

            model_name = (
                model.get("name", "model.bin").replace("/", "_").replace("\\", "_")
            )
            file_path = os.path.join(download_dir, model_name)
            try:
                print(f"Downloading: {model_name} -> {file_path}")
                download_response = requests.get(
                    model_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                    stream=True,
                    timeout=30,
                )

                if download_response.status_code == 200:
                    with open(file_path, "wb") as f:
                        for chunk in download_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    downloaded_files.append(file_path)
                    print(f"Successfully downloaded: {file_path}")
                else:
                    print(f"Download failed for {model_name}: {download_response.status_code}")

            except Exception as e:
                print(f"Error downloading {model_name}: {e}")

        # === Response to Client ===
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = f"""
        <h1 style="color: green;">Successfully downloaded!</h1>
        <p><strong>Tone Type:</strong> {tone_type}</p>
        <p><strong>Download Directory:</strong> {download_dir}</p>
        <p><strong>Downloaded Files:</strong></p>
        <ul>
        {"".join(f"<li>{f}</li>" for f in downloaded_files)}
        </ul>
        <hr>
        <p>
            <a href="javascript:void(0)" onclick="window.close();">
                Close this window
            </a>
        </p>
        """
        self.wfile.write(html.encode())
        self.server.shutdown_event.set()


# === Start Local Server ===
def start_server(client_id, port, interface, ir_dir, nam_dir):
    # Determine Redirect URI based on IP
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
        "state": state,
        "prompt": "select_tone",
    }
    query_string = urllib.parse.urlencode(params)
    authorize_url = f"{AUTHORIZE_URL}?{query_string}"

    print(f"\nAuthorization URL:\n{authorize_url}\n")

    Handler = CallbackHandler
    with socketserver.TCPServer(("", port), Handler) as httpd:
        httpd.session = {
            "t3k_state": state, 
            "client_id": client_id, 
            "redirect_uri": redirect_uri,
            "ir_dir": ir_dir,
            "nam_dir": nam_dir
        }
        httpd.shutdown_event = threading.Event()

        print(f"Local server running on {ip_addr}:{port}")
        print("Waiting for callback... (open the browser if you are not logged in)")

        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()

        httpd.shutdown_event.wait()
        httpd.shutdown()
        httpd.server_close()
        print("\nOAuth flow completed. Server stopped.")


# === Main Execution ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tone3000 Model Downloader for Zynthian")
    parser.add_argument(
        "--client_id", 
        required=True, 
        help="The OAuth Client ID provided by Tone3000"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=63342, 
        help="Local port for the callback server (default: 63342)"
    )
    parser.add_argument(
        "--interface", 
        type=str, 
        default="eth0", 
        help="Network interface to determine the IP address (default: eth0)"
    )
    parser.add_argument(
        "--ir_dir", 
        type=str, 
        default=DEFAULT_IR_DIR, 
        help=f"Directory for IR files (default: {DEFAULT_IR_DIR})"
    )
    parser.add_argument(
        "--nam_dir", 
        type=str, 
        default=DEFAULT_NAM_DIR, 
        help=f"Directory for NAM profiles (default: {DEFAULT_NAM_DIR})"
    )
    
    args = parser.parse_args()
    
    start_server(
        args.client_id, 
        args.port, 
        args.interface, 
        args.ir_dir, 
        args.nam_dir
    )
