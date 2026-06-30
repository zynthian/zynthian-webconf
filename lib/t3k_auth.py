# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Login Handler
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

if not hasattr(t3k_auth, '_initialized'):
    # PKCE & state generation
    code_verifier = secrets.token_urlsafe(128)
    code_challenge_hash = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge_hash).decode("utf-8").rstrip("=")
    state_token = secrets.token_urlsafe(32)

    t3k_auth.code_verifier = code_verifier
    t3k_auth.code_challenge = code_challenge
    t3k_auth.state_token = state_token

    t3k_auth._initialized = True
