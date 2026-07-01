# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Tone 3000 OAuth configuration
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
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            # Nur einmal initialisieren
            object.__setattr__(self, '_code_verifier', secrets.token_urlsafe(128))
            code_challenge_hash = hashlib.sha256(self._code_verifier.encode("utf-8")).digest()
            object.__setattr__(self, '_code_challenge', base64.urlsafe_b64encode(code_challenge_hash).decode("utf-8").rstrip("="))
            object.__setattr__(self, '_state_token', secrets.token_urlsafe(32))

            # Markiere als initialisiert
            object.__setattr__(self, '_initialized', True)

    # --- Properties für die Werte ---
    @property
    def code_challenge(self):
        return self._code_challenge

    @property
    def state_token(self):
        return self._state_token

    @property
    def code_verifier(self):
        return self._code_verifier

    # --- Verhindere Überschreibung der Werte ---
    def __setattr__(self, name, value):
        # Verhindere Änderung der sensiblen Werte nach Initialisierung
        if name in ('_code_verifier', '_code_challenge', '_state_token') and hasattr(self, '_initialized'):
            raise AttributeError(f"Cannot modify {name} after initialization")
        super().__setattr__(name, value)

pkce_manager = PKCEManager()

def __getattr__(name):
    return getattr(pkce_manager, name)

if __name__ == "__main__":
    import t3k_auth
    print("State Token:", t3k_auth.state_token)
    print("Code Challenge:", t3k_auth.code_challenge)
    print("Code Verifier:", t3k_auth.code_verifier)
    import t3k_auth
    print("State Token:", t3k_auth.state_token)
    print("Code Challenge:", t3k_auth.code_challenge)
    print("Code Verifier:", t3k_auth.code_verifier)

