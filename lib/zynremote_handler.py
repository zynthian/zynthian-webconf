# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Zynthian Remote: same-origin bridges for the remote page (mockup/zynremote.html)
#
# The remote page talks to several local services. Bridging them through webconf
# makes everything reachable from the page's own origin, so it works the same
# over http (ws://) and https (wss://), with a single certificate:
#
#   /zynremote/config   => JSON describing what this zynthian offers (viewer, audio, ...)
#   /zynws              => websocket of zynthian-ui (ws://localhost:8370): keys, MIDI, LEDs
#   /zynremote/vnc      => VNC server of the display (localhost:5900, x11vnc), for noVNC
#   /zynremote/vnc1     => VNC server of the processor GUIs (display :1, localhost:5901), for noVNC
#   /zynremote/audio/   => MediaMTX (http://localhost:8889): audio stream (WHEP) when available
#
# Copyright (C) 2026 Fernando Moyano <fernando@zynthian.org>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# For a full copy of the GNU General Public License see the LICENSE.txt file.
#
# ********************************************************************

import json
import socket
import logging

import tornado.web
import tornado.ioloop
import tornado.websocket
import tornado.httpclient
from tornado.iostream import StreamClosedError
from tornado.tcpclient import TCPClient

UI_WS_PORT = 8370       # zynthian-ui websocket server
VNC_PORT = 5900         # x11vnc mirroring the display (vncserver0 service)
KASMVNC_PORT = 8443     # KasmVNC web server (containerized zynthian)
VNC1_PORT = 5901        # VNC server of display :1, the processor GUIs (vncserver1 service, TigerVNC)
KASMVNC1_PORT = 8444    # KasmVNC web server of display :1 (containerized zynthian)
AUDIO_PORT = 8889       # MediaMTX WebRTC/WHEP server
AUDIO_PATH = "zynstream"


def port_open(port, host="127.0.0.1", timeout=0.2):
    """True if something listens on the local TCP port (quick: refused at once if not)"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


# ------------------------------------------------------------------------------
# Configuration for the remote page
# ------------------------------------------------------------------------------

class ZynremoteConfigHandler(tornado.web.RequestHandler):

    def get(self):
        if port_open(KASMVNC_PORT):
            # KasmVNC has its own web client: the page embeds it (different port, own certificate)
            vnc = "kasm"
        elif port_open(VNC_PORT):
            vnc = "novnc"
        else:
            vnc = None
        # Processor GUIs (display :1): only while enabled in the UI (vncserver1 service)
        if port_open(KASMVNC1_PORT):
            gui_url = f"https://{self.request.host_name}:{KASMVNC1_PORT}/?resize=remote"
        elif port_open(VNC1_PORT):
            gui_url = "/novnc/vnc.html?path=zynremote/vnc1&autoconnect=1&resize=remote&reconnect=1"
        else:
            gui_url = None
        config = {
            "vnc": vnc,
            "gui_url": gui_url,
            "kasm_url": f"https://{self.request.host_name}:{KASMVNC_PORT}/?resize=scale",
            "novnc_path": "/zynremote/vnc",
            "ws_path": "/zynws",
            "ws": port_open(UI_WS_PORT),
            "audio_path": f"/zynremote/audio/{AUDIO_PATH}/?muted=false" if port_open(AUDIO_PORT) else None
        }
        self.set_header("Content-Type", "application/json")
        self.set_header("Cache-Control", "no-store")
        self.write(json.dumps(config))


# ------------------------------------------------------------------------------
# Websocket bridge to zynthian-ui
# ------------------------------------------------------------------------------

class ZynremoteUIWebSocketBridge(tornado.websocket.WebSocketHandler):
    """Browser websocket <=> zynthian-ui websocket server, message by message"""

    upstream = None

    async def open(self):
        try:
            self.upstream = await tornado.websocket.websocket_connect(f"ws://127.0.0.1:{UI_WS_PORT}")
        except Exception as e:
            logging.warning(f"Zynremote: can't connect to the UI websocket => {e}")
            self.close(1011, "UI websocket not available")
            return
        tornado.ioloop.IOLoop.current().spawn_callback(self.pump_upstream)

    async def pump_upstream(self):
        upstream = self.upstream
        while True:
            msg = await upstream.read_message()
            if msg is None:
                break
            try:
                await self.write_message(msg, binary=isinstance(msg, bytes))
            except tornado.websocket.WebSocketClosedError:
                break
        upstream.close()
        self.close()

    def on_message(self, message):
        if self.upstream:
            self.upstream.write_message(message, binary=isinstance(message, bytes))

    def on_close(self):
        if self.upstream:
            self.upstream.close()
            self.upstream = None


# ------------------------------------------------------------------------------
# Websocket <=> TCP bridge to the VNC server (like websockify)
# ------------------------------------------------------------------------------

class ZynremoteVNCBridge(tornado.websocket.WebSocketHandler):
    """noVNC (binary websocket) <=> VNC server (TCP)"""

    stream = None

    def initialize(self, port=VNC_PORT):
        self.vnc_port = port

    def select_subprotocol(self, subprotocols):
        return "binary" if "binary" in subprotocols else None

    async def open(self):
        try:
            self.stream = await TCPClient().connect("127.0.0.1", self.vnc_port)
            self.stream.set_nodelay(True)
        except Exception as e:
            logging.warning(f"Zynremote: can't connect to the VNC server => {e}")
            self.close(1011, "VNC server not available")
            return
        tornado.ioloop.IOLoop.current().spawn_callback(self.pump_vnc)

    async def pump_vnc(self):
        stream = self.stream
        try:
            while True:
                data = await stream.read_bytes(65536, partial=True)
                # Wait until sent: keeps the buffering bounded if the browser is slow
                await self.write_message(data, binary=True)
        except (StreamClosedError, tornado.websocket.WebSocketClosedError):
            pass
        stream.close()
        self.close()

    async def on_message(self, message):
        if self.stream:
            try:
                await self.stream.write(message if isinstance(message, bytes) else message.encode())
            except StreamClosedError:
                self.close()

    def on_close(self):
        if self.stream:
            self.stream.close()
            self.stream = None


# ------------------------------------------------------------------------------
# HTTP proxy to MediaMTX (WHEP signaling + reader page). Media goes by WebRTC (UDP), not here.
# ------------------------------------------------------------------------------

class ZynremoteAudioProxy(tornado.web.RequestHandler):

    SUPPORTED_METHODS = ("GET", "POST", "PATCH", "DELETE", "OPTIONS")
    PREFIX = "/zynremote/audio"
    REQ_HEADERS = ("Content-Type", "If-Match", "Accept", "Authorization")
    RESP_HEADERS = ("Content-Type", "ETag", "Link", "Accept-Patch", "Cache-Control",
                    "Access-Control-Allow-Origin", "Access-Control-Allow-Methods",
                    "Access-Control-Allow-Headers", "Access-Control-Expose-Headers")

    async def proxy(self, path):
        url = f"http://127.0.0.1:{AUDIO_PORT}/{path}"
        if self.request.query:
            url += "?" + self.request.query
        headers = {h: self.request.headers[h] for h in self.REQ_HEADERS if h in self.request.headers}
        body = self.request.body if self.request.method in ("POST", "PATCH") else None
        try:
            resp = await tornado.httpclient.AsyncHTTPClient().fetch(
                url, method=self.request.method, headers=headers, body=body,
                follow_redirects=False, raise_error=False, allow_nonstandard_methods=True,
                request_timeout=10)
        except Exception as e:
            logging.warning(f"Zynremote: audio server not available => {e}")
            self.set_status(502)
            return
        if resp.code == 599:
            self.set_status(502)
            return
        self.set_status(resp.code, resp.reason)
        for h in self.RESP_HEADERS:
            if h in resp.headers:
                self.set_header(h, resp.headers[h])
        # WHEP session URL (absolute path) => keep it under this proxy
        location = resp.headers.get("Location")
        if location:
            self.set_header("Location", self.PREFIX + location if location.startswith("/") else location)
        if resp.body and resp.code not in (204, 304):
            self.write(resp.body)

    async def get(self, path):
        await self.proxy(path)

    async def post(self, path):
        await self.proxy(path)

    async def patch(self, path):
        await self.proxy(path)

    async def delete(self, path):
        await self.proxy(path)

    async def options(self, path):
        await self.proxy(path)
