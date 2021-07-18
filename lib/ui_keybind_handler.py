# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# UI Keyboard Binding Handler
#
# Copyright (C) 2019 Brian Walton <brian@riban.co.uk>
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
from collections import OrderedDict

from lib.zynthian_config_handler import ZynthianBasicHandler
from zyngui.zynthian_gui_keybinding import zynthian_gui_keybinding

# ------------------------------------------------------------------------------
# UI Configuration
# ------------------------------------------------------------------------------


class UiKeybindHandler(ZynthianBasicHandler):

    @tornado.web.authenticated
    def get(self, errors=None):
        if self.reload_key_binding_flag:
            self.reload_key_binding()

        zynthian_gui_keybinding.getInstance().load()
        config = OrderedDict([])
        config['UI_KEYBINDING_MAP'] = zynthian_gui_keybinding.getInstance().config['map']
        config['UI_KEYBINDING_ENABLED'] = zynthian_gui_keybinding.getInstance().isEnabled()

        super().get("ui_keybind.html", "Keyboard Binding", config, errors)

    @tornado.web.authenticated
    def post(self):
        action = self.get_argument('UI_KEYBINDING_ACTION')
        if action:
            errors = {
                'SAVE': lambda: self.do_save(),
                'RESET': lambda: self.do_reset(),
            }[action]()
        self.get(errors)

    def do_save(self):
        try:
            data = tornado.escape.recursive_unicode(self.request.arguments)

            enable = False
            zynthian_gui_keybinding.getInstance().reset_modifiers()
            for key, value in data.items():
                try:
                    if key == "enable_keybinding":
                        logging.debug("Key-binding enabled!")
                        enable = True
                    else:
                        logging.debug(
                            "Map Action '{}' => {}".format(key, value[0]))
                        self.update_map_entry(key, value[0])

                except Exception as e:
                    pass

            zynthian_gui_keybinding.getInstance().enable(enable)
            zynthian_gui_keybinding.getInstance().save()
            self.reload_key_binding_flag = True

        except Exception as e:
            logging.error("Saving keyboard binding failed: {}".format(e))
            return format(e)

    def do_reset(self):
        try:
            zynthian_gui_keybinding.getInstance().reset_config()
            zynthian_gui_keybinding.getInstance().save()
            self.reload_key_binding_flag = True

        except Exception as e:
            logging.error(
                "Resetting keyboard binding to defaults failed: {}".format(e))
            return format(e)

    def update_map_entry(self, param, value):
        action, param = param.split(':')
        try:
            if param == "keysym":
                logging.debug(
                    "Update binding for {}: {}".format(action, value))
                zynthian_gui_keybinding.getInstance().set_binding_keysym(action, value)
            else:
                logging.debug("Add modifier for {}: {}".format(action, param))
                zynthian_gui_keybinding.getInstance().add_binding_modifier(action, param)

        except Exception as e:
            logging.error("Failed to set binding for {}: {}".format(action, e))


# --------------------------------------------------------------------
