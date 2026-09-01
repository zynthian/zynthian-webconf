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


import os
import logging
import tornado.web
import urllib.parse
from bs4 import BeautifulSoup

from lib.zynthian_config_handler import ZynthianBasicHandler
from zyngui.zynthian_gui_help import zynthian_gui_help

# ------------------------------------------------------------------------------
# UI Configuration
# ------------------------------------------------------------------------------

class HelpHandler(ZynthianBasicHandler):

    help_files_dpath = os.environ.get('ZYNTHIAN_WEBCONF_DIR', "/zynthian/zynthian-webconf") + "/help"
    ui_dir = os.environ.get('ZYNTHIAN_UI_DIR', "/zynthian/zynthian-ui")

    @tornado.web.authenticated
    def get(self, subdir=None, html_file=None, errors=None):
        if subdir is None and html_file is None:
            subdir = ""
            html_file = ""
            html = self.get_body(zynthian_gui_help.get_index())
            index = True
        else:
            html = self.get_content(subdir, html_file)
            index = False
        
        config = {
            "subdir": subdir,
            "html_file": html_file,
            "content": html,
            "index": index
        }
        super().get("help.html", "Help", config, errors)

    @tornado.web.authenticated
    def post(self, subdir, html_file):
        self.get(subdir, html_file)

    def get_content(self, subdir, html_file):
        try:
            fpath = f"{self.help_files_dpath}/{subdir}/{html_file}"
            with open(fpath, "r") as f:
                html = f.read()
                try:
                    html = self.get_body(html, subdir, fname= os.path.splitext(html_file)[0])
                except Exception as e:
                    logging.error(e)

        except:
            html = f"<h3>Content '{subdir}/{html_file}' not found!</h3>"
        return html

    def get_body(self, html, subdir=None, fname=None):
        soup = BeautifulSoup(html, "html.parser")
        # Get list of css files
        css_fpaths = []
        for link in soup.find_all("link", href=True):
            href = link["href"]  #.replace(self.ui_dir + "/help/", "")
            css_fpath = "/help_files/"
            if subdir:
                css_fpath += subdir + "/"
            css_fpath += urllib.parse.quote(href)
            link["href"] = css_fpath
            css_fpaths.append(css_fpath)
        # Fix img's src'
        for img in soup.find_all("img", src=True):
            src = "/help_files/"
            if subdir:
                src += subdir + "/"
            img["src"] = src + urllib.parse.quote(img["src"])
        # Fix link's href
        for link in soup.find_all("a", href=True):
            href = link["href"].replace(self.ui_dir, "")
            link["href"] = urllib.parse.quote(href)
        # Generate html adding css
        html = ""
        for css_fpath in css_fpaths:
            html += f"<link rel=\"stylesheet\" href=\"{css_fpath}\">\n"
        html += f"<link rel=\"stylesheet\" href=\"/help_files/style_webconf.css\">\n"
        html += "<div class=\"help_ui\">\n"
        if fname:
            fpath = f"{subdir}/screenshots/{fname}"
            if os.path.isfile(self.help_files_dpath + "/" + fpath + ".mp4"):
                html += f"<video class='screenshot' controls autoplay muted loop><source src=\"/help_files/{fpath}.mp4\" type='video/mp4'></video>\n"
            elif os.path.isfile(self.help_files_dpath + "/" + fpath + ".png"):
                html += f"<img class='screenshot' src=\"/help_files/{fpath}.png\"/>\n"
        html += soup.body.decode_contents()
        html += "\n</div>"
        return html

