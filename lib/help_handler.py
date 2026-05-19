# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# UI Configuration Handler
#
# Copyright (C) 2017 Fernando Moyano <jofemodo@zynthian.org>
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


import logging

import tornado.web
from collections import OrderedDict
import urllib.parse

from lib.zynthian_config_handler import ZynthianBasicHandler
from bs4 import BeautifulSoup
from zyngui.zynthian_gui_help import zynthian_gui_help

# ------------------------------------------------------------------------------
# UI Configuration
# ------------------------------------------------------------------------------

class HelpHandler(ZynthianBasicHandler):

    @tornado.web.authenticated
    def get(self, errors=None):
        try:
            help_page = self.get_argument("target")
        except:
            help_page = "Index"
        
        config = {
            "content": self.get_help(help_page),
            "index": help_page == "Index"
        }
        super().get("help.html", "Help", config, errors)

    @tornado.web.authenticated
    def post(self):
        self.get()

    def get_help(self, path=None):
        try:
            with open(path, "r") as f:
                html = f.read()
        except:
            html = zynthian_gui_help.get_index()
        return self.get_body(html)

    def get_body(self, html):
        soup = BeautifulSoup(html, "html.parser")
        for link in soup.find_all("a", href=True):
            original_target = link["href"]
            encoded = urllib.parse.quote(original_target)
            link["href"] = f"help?target={encoded}"
        return soup.body.decode_contents()
