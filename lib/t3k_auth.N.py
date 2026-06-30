# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Login Handler (mit Klasse und globaler Instanz)
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

import secrets
import hashlib
import base64


class PKCEManager:
    """
    Singleton-Klasse zur Verwaltung von PKCE-Parametern.
    Initialisierung erfolgt nur einmal, auch bei mehrfachem Import.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            # Nur einmal initialisieren
            self._code_verifier = secrets.token_urlsafe(128)
            code_challenge_hash = hashlib.sha256(self._code_verifier.encode("utf-8")).digest()
            self._code_challenge = base64.urlsafe_b64encode(code_challenge_hash).decode("utf-8").rstrip("=")
            self._state_token = secrets.token_urlsafe(32)

            # Markiere als initialisiert
            self._initialized = True

    # --- Getter für die Werte ---
    def get_code_challenge(self):
        return self._code_challenge

    def get_state_token(self):
        return self._state_token

    def get_code_verifier(self):
        return self._code_verifier

    # --- Verhindere Überschreibung der Werte ---
    def __setattr__(self, name, value):
        # Verhindere Änderung der sensiblen Werte nach Initialisierung
        if name in ('_code_verifier', '_code_challenge', '_state_token') and hasattr(self, '_initialized'):
            raise AttributeError(f"Cannot modify {name} after initialization")
        super().__setattr__(name, value)


# --- Globale Instanz: t3k_auth ---
# Diese Variable ist jetzt global im Modul und kann von anderen Modulen importiert werden
t3k_auth = PKCEManager()
