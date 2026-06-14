import base64
import hashlib
import http.server
import os
import secrets
import socketserver
import threading
import urllib.parse
import webbrowser
from urllib.parse import parse_qs, urlparse

import requests

# === Konfiguration ===
CLIENT_ID = "t3k_pub_jN64LmaLWMdcqlnyfFxFtIzGbDfnfvPr"
REDIRECT_URI = "http://localhost:8000/callback"
AUTHORIZE_URL = "https://www.tone3000.com/api/v1/oauth/authorize"
TOKEN_URL = "https://www.tone3000.com/api/v1/oauth/token"

# === 1. PKCE: Code Verifier generieren ===
code_verifier = secrets.token_urlsafe(128)

# === 2. Code Challenge (S256) ===
code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8").rstrip("=")

# === 3. State generieren ===
state = secrets.token_urlsafe(32)

# === 4. OAuth-Parameter ===
params = {
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "response_type": "code",
    "code_challenge": code_challenge,
    "code_challenge_method": "S256",
    "state": state,
    "prompt": "select_tone",
}

# === 5. URL-encode ===
query_string = urllib.parse.urlencode(params)

# === 6. Vollständige URL ===
authorize_url = f"{AUTHORIZE_URL}?{query_string}"

# === 7. Öffne im Browser ===
print("🌐 Öffne den OAuth-Flow im Browser...")
print("👉 Bitte wähle einen Tone aus und bestätige.")
print(authorize_url)
webbrowser.open(authorize_url)


# === 8. Lokaler Webserver für Callback ===
class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse URL
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        code = query_params.get("code", [None])[0]
        state = query_params.get("state", [None])[0]
        tone_id = query_params.get("tone_id", [None])[0]
        canceled = query_params.get("canceled", [None])[0] == "true"

        # Prüfe State
        if state != self.server.session.get("t3k_state"):
            print("❌ State mismatch. Possible CSRF attack.")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"State mismatch. Possible CSRF attack.")
            self.server.shutdown_event.set()
            return

        if canceled:
            print("⏸️ Benutzer hat den Flow abgebrochen.")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(
                b"<h1>Abgebrochen</h1><p>Der Benutzer hat den Flow abgebrochen.</p>"
            )
            self.server.shutdown_event.set()
            return

        if not code:
            print("❌ Kein Code erhalten.")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Kein Code erhalten.")
            self.server.shutdown_event.set()
            return

        print(f"✅ Code erhalten: {code}")
        print(f"✅ Tone-ID: {tone_id}")

        # === Token Austausch ===
        try:
            print("📤 Sende Token-Anfrage an Tone3000...")
            print(f"  - client_id: {CLIENT_ID}")
            print(f"  - redirect_uri: {REDIRECT_URI}")
            print(f"  - code: {code}")
            print(
                f"  - code_verifier: {code_verifier[:10]}..."
            )  # nur erste 10 Zeichen zeigen

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

            print(f"📬 Antwort-Status: {token_response.status_code}")
            print(f"📬 Antwort-Body: {token_response.text}")

            if token_response.status_code != 200:
                print("❌ Token-Austausch fehlgeschlagen!")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(
                    f"<h1>Fehler beim Token-Austausch</h1><p>Status: {token_response.status_code}</p><pre>{token_response.text}</pre>".encode()
                )
                self.server.shutdown_event.set()
                return

            token_data = token_response.json()
            access_token = token_data["access_token"]
            print(f"✅ Token erfolgreich erhalten: {access_token[:20]}...")

        except Exception as e:
            print(f"❌ Ausnahme beim Token-Austausch: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"<h1>Fehler</h1><p>{e}</p>".encode())
            self.server.shutdown_event.set()
            return

        # === Tone-Metadaten abrufen ===
        try:
            print("📥 Lade Tone-Metadaten...")
            tone_response = requests.get(
                f"https://www.tone3000.com/api/v1/tones/{tone_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            print(f"  Tone-Status: {tone_response.status_code}")
            print(f"  Tone-Body: {tone_response.text}")

            if tone_response.status_code != 200:
                print("❌ Fehler beim Abrufen der Tone-Metadaten.")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(
                    f"<h1>Fehler</h1><p>Tone-Metadaten nicht verfügbar</p><pre>{tone_response.text}</pre>".encode()
                )
                self.server.shutdown_event.set()
                return

            tone_data = tone_response.json()
            # Prüfe, ob es sich um einen IR-Tone handelt
            is_ir_tone = (
                tone_data.get("gear") == "ir" or tone_data.get("platform") == "ir"
            )

            # Sammle alle aX_models_count-Werte
            a_models_count = [
                value
                for key, value in tone_data.items()
                if key.startswith("a") and key.endswith("_models_count")
            ]

            # Wenn alle 0 und IR-Tone → setze tone_name = "IR"
            if is_ir_tone and all(count == 0 for count in a_models_count):
                tone_name = "IR"
            else:
                tone_name = "NAM"

            print(f"✅ Tone: {tone_name}")

        except Exception as e:
            print(f"❌ Fehler beim Abrufen der Tone-Metadaten: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"<h1>Fehler</h1><p>Tone-Metadaten: {e}</p>".encode())
            self.server.shutdown_event.set()
            return

        # === Modelle abrufen ===
        try:
            print("📥 Lade Modelle...")
            models_response = requests.get(
                "https://www.tone3000.com/api/v1/models",
                params={"tone_id": tone_id},
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            print(f"  Modelle-Status: {models_response.status_code}")
            print(f"  Modelle-Body (raw): {models_response.text}")

            if models_response.status_code != 200:
                print("❌ Fehler beim Abrufen der Modelle.")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(
                    f"<h1>Fehler</h1><p>Modelle nicht verfügbar</p><pre>{models_response.text}</pre>".encode()
                )
                self.server.shutdown_event.set()
                return

            models_data = models_response.json()
            print(f"✅ JSON-Struktur: {models_data}")

            # Extrahiere die Liste der Modelle
            models = models_data.get("data", [])
            if not isinstance(models, list):
                print(
                    "⚠️ Warnung: 'data' ist keine Liste. Versuche als Liste zu behandeln..."
                )
                models = models

            print(f"✅ {len(models)} Modelle gefunden.")

        except Exception as e:
            print(f"❌ Fehler beim Abrufen der Modelle: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"<h1>Fehler</h1><p>Modelle: {e}</p>".encode())
            self.server.shutdown_event.set()
            return

        # === Download der Modelle ===
        download_dir = f"downloads/{tone_name}"
        os.makedirs(download_dir, exist_ok=True)

        downloaded_files = []
        for model in models:
            model_url = model.get("model_url")
            if not model_url:
                print("⚠️ Kein model_url für Modell, überspringe...")
                continue

            model_name = (
                model.get("name", "model.bin").replace("/", "_").replace("\\", "_")
            )
            file_path = os.path.join(download_dir, model_name)
            try:
                print(f"📥 Download: {model_name} → {file_path}")

                # ✅ Wichtig: Authorization-Header beim Download verwenden!
                download_response = requests.get(
                    model_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                    stream=True,
                    timeout=30,
                )

                if download_response.status_code != 200:
                    print(
                        f"❌ Download fehlgeschlagen: {download_response.status_code}"
                    )
                    print(f"  Antwort: {download_response.text}")
                    continue

                with open(file_path, "wb") as f:
                    for chunk in download_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                downloaded_files.append(file_path)
                print(f"✅ Erfolgreich heruntergeladen: {file_path}")

            except Exception as e:
                print(f"❌ Fehler beim Herunterladen von {model_name}: {e}")

        # === Antwort an den Client ===
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = f"""
        <h1>✅ Erfolgreich heruntergeladen!</h1>
        <p><strong>Tone:</strong> {tone_name}</p>
        <p><strong>Download-Verzeichnis:</strong> {download_dir}</p>
        <p><strong>Heruntergeladene Dateien:</strong></p>
        <ul>
        {"".join(f"<li>{f}</li>" for f in downloaded_files)}
        </ul>
        <p><a href="/">Zurück</a></p>
        """
        self.wfile.write(html.encode())

        # === Server beenden ===
        self.server.shutdown_event.set()


# === Starte lokalen Server ===
def start_server():
    PORT = 8000
    Handler = CallbackHandler

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.session = {"t3k_state": state}
        httpd.shutdown_event = threading.Event()

        print(f"\n🌐 Lokaler Server läuft auf http://localhost:{PORT}")
        print(
            "💡 Warte auf Callback... (öffne den Browser, wenn du noch nicht eingeloggt bist)"
        )

        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()

        # Warte auf Callback
        httpd.shutdown_event.wait()

        httpd.shutdown()
        httpd.server_close()
        print("\n✅ OAuth-Flow abgeschlossen. Server gestoppt.")


# === Starte alles ===
if __name__ == "__main__":
    start_server()
