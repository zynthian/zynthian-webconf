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
from collections import OrderedDict

from lib.zynthian_config_handler import ZynthianConfigHandler

# ------------------------------------------------------------------------------
# UI Configuration
# ------------------------------------------------------------------------------


class UiConfigHandler(ZynthianConfigHandler):

    font_families = [
        "Audiowide",
        "Helvetica",
        "Economica",
        "Orbitron",
        "Abel"
    ]

    @tornado.web.authenticated
    def get(self, errors=None):
        touch_navigation = os.environ.get('ZYNTHIAN_UI_TOUCH_NAVIGATION', "")
        if touch_navigation not in ("", "v5_keypad_left", "v5_keypad_right"):
            touch_navigation = "v5_keypad_left"

        config = {
            'ZYNTHIAN_UI_POWER_SAVE_MINUTES': {
                'type': 'text',
                'title': 'Power-Save delay (minutes)',
                'value': os.environ.get('ZYNTHIAN_UI_POWER_SAVE_MINUTES', '60')
            },
            'ZYNTHIAN_UI_RESTORE_LAST_STATE': {
                'type': 'boolean',
                'title': 'Restore last state on startup',
                'value': os.environ.get('ZYNTHIAN_UI_RESTORE_LAST_STATE', '1')
            },
            'ZYNTHIAN_UI_SNAPSHOT_MIXER_SETTINGS': {
                'type': 'boolean',
                'title': 'Audio levels on snapshots',
                'value': os.environ.get('ZYNTHIAN_UI_SNAPSHOT_MIXER_SETTINGS', '0')
            },
            'ZYNTHIAN_UI_PRESET_PRELOAD': {
                'type': 'boolean',
                'title': 'Preload Presets',
                'value': os.environ.get('ZYNTHIAN_UI_PRESET_PRELOAD', '1')
           },

            'ZYNTHIAN_VNCSERVER_ENABLED': {
                'type': 'boolean',
                'title': 'Enable VNC',
                'value': os.environ.get('ZYNTHIAN_VNCSERVER_ENABLED', '0'),
            },
            '_SECTION_UI_GRAPHICS_': {
                'type': 'html',
                'content': "<h3>Graphics & Usability</h3>",
            },
            'ZYNTHIAN_UI_GRAPHIC_LAYOUT': {
                'type': 'select',
                'title': 'Controller widgets layout',
                'value': os.environ.get('ZYNTHIAN_UI_GRAPHIC_LAYOUT', ''),
                'options': ["", "V4", "Z2"],
                'option_labels': {
                    '': "Auto",
                    'V4': "Knobs at corners (V1-V4)",
                    'Z2': "Knobs at right side (Z2, V5, MINI)",
                },
                'advanced': True
            },
            'ZYNTHIAN_UI_TOUCH_NAVIGATION': {
                'type': 'select',
                'title': 'Touch Navigation',
                'value': touch_navigation,
                'options': ['', 'v5_keypad_left', 'v5_keypad_right'],
                'option_labels': {
                    '': 'None',
                    'v5_keypad_left': 'V5 keypad on left',
                    'v5_keypad_right': 'V5 keypad on right'
                },
            },
            'ZYNTHIAN_UI_ENABLE_CURSOR': {
                'type': 'boolean',
                'title': 'Enable cursor',
                'value': os.environ.get('ZYNTHIAN_UI_ENABLE_CURSOR', '0'),
                'advanced': True
            },
            'ZYNTHIAN_UI_VISIBLE_MIXER_STRIPS': {
                'type': 'select',
                'title': 'Visible mixer strips',
                'value':  os.environ.get('ZYNTHIAN_UI_VISIBLE_MIXER_STRIPS', "0"),
                'options': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16'],
                'option_labels': {
                    '0': 'Automatic',
                    '1': '1',
                    '2': '2',
                    '3': '3',
                    '4': '4',
                    '5': '5',
                    '6': '6',
                    '7': '7',
                    '8': '8',
                    '9': '9',
                    '10': '10',
                    '11': '11',
                    '12': '12',
                    '13': '13',
                    '14': '14',
                    '15': '15',
                    '16': '16'
                },
                'advanced': True
            },
            'ZYNTHIAN_UI_SWITCH_BOLD_MS': {
                'type': 'text',
                'title': 'Bold-push time (ms)',
                'value': os.environ.get('ZYNTHIAN_UI_SWITCH_BOLD_MS', '300'),
                'advanced': True
            },
            'ZYNTHIAN_UI_SWITCH_LONG_MS': {
                'type': 'text',
                'title': 'Long-push time (ms)',
                'value': os.environ.get('ZYNTHIAN_UI_SWITCH_LONG_MS', '2000'),
                'advanced': True
            },
            '_SECTION_UI_COLORS_': {
                'type': 'html',
                'content': "<h3>Font & Colors</h3>",
            },
            'ZYNTHIAN_UI_FONT_SIZE': {
                'type': 'text',
                'title': 'Font size',
                        'value': os.environ.get('ZYNTHIAN_UI_FONT_SIZE', "16")
            },
            'ZYNTHIAN_UI_FONT_FAMILY': {
                'type': 'select',
                'title': 'Font family',
                'value': os.environ.get('ZYNTHIAN_UI_FONT_FAMILY', "Audiowide"),
                'options': self.font_families,
                'advanced': True
            },
            'ZYNTHIAN_UI_COLOR_INFO': {
                'type': 'text',
                'title': 'Info color',
                'value': os.environ.get('ZYNTHIAN_UI_COLOR_INFO', "#8080ff"),
                'advanced': True
            },
            'ZYNTHIAN_UI_COLOR_ERROR': {
                'type': 'text',
                'title': 'Error color',
                'value': os.environ.get('ZYNTHIAN_UI_COLOR_ERROR', "#ff0000"),
                'advanced': True
            },
            'ZYNTHIAN_UI_COLOR_MIDI': {
                'type': 'text',
                'title': 'MIDI color',
                'value': os.environ.get('ZYNTHIAN_UI_COLOR_MIDI', "#9090ff"),
                'advanced': True
            },
            'ZYNTHIAN_UI_COLOR_ALT': {
                'type': 'text',
                'title': 'Alternate color',
                'value': os.environ.get('ZYNTHIAN_UI_COLOR_ALT', "#ff00ff"),
                'advanced': True
            },
            'ZYNTHIAN_UI_COLOR_ALT2': {
                'type': 'text',
                'title': '2nd Alternate color',
                'value': os.environ.get('ZYNTHIAN_UI_COLOR_ALT2', "#ff9000"),
                'advanced': True
            },
            'ZYNTHIAN_UI_COLOR_BG': {
                'type': 'text',
                'title': 'Background color',
                'value': os.environ.get('ZYNTHIAN_UI_COLOR_BG', "#000000"),
                'advanced': True
            },
            'ZYNTHIAN_UI_COLOR_TX': {
                'type': 'text',
                'title': 'Text color',
                'value': os.environ.get('ZYNTHIAN_UI_COLOR_TX', "#ffffff"),
                'advanced': True
            },
            'ZYNTHIAN_UI_COLOR_TX_OFF': {
                'type': 'text',
                'title': 'Text-Off color',
                'value': os.environ.get('ZYNTHIAN_UI_COLOR_TX_OFF', "#e0e0e0"),
                'advanced': True
            },
            'ZYNTHIAN_UI_COLOR_ON': {
                'type': 'text',
                'title': 'On color',
                'value': os.environ.get('ZYNTHIAN_UI_COLOR_ON', "#ff0000"),
                'advanced': True
            },
            'ZYNTHIAN_UI_COLOR_LOW_ON': {
                'type': 'text',
                'title': 'Low-On color',
                'value': os.environ.get('ZYNTHIAN_UI_COLOR_LOW_ON', "#b00000"),
                'advanced': True
            },
            'ZYNTHIAN_UI_COLOR_OFF': {
                'type': 'text',
                'title': 'Off color',
                'value': os.environ.get('ZYNTHIAN_UI_COLOR_OFF', "#5a626d"),
                'advanced': True
            },
            'ZYNTHIAN_UI_COLOR_HL': {
                'type': 'text',
                'title': 'Highlight color',
                'value': os.environ.get('ZYNTHIAN_UI_COLOR_HL', "#00b000"),
                'advanced': True
            },
            'ZYNTHIAN_UI_COLOR_ML': {
                'type': 'text',
                'title': 'Midlight color',
                'value': os.environ.get('ZYNTHIAN_UI_COLOR_ML', "#f0f000"),
                'advanced': True
            },
            'ZYNTHIAN_UI_COLOR_PANEL_BG': {
                'type': 'text',
                'title': 'Panel background color',
                'value': os.environ.get('ZYNTHIAN_UI_COLOR_PANEL_BG', "#3a424d"),
                'advanced': True
            },
            'ZYNTHIAN_UI_COLOR_PANEL_HL': {
                'type': 'text',
                'title': 'Panel highlight color',
                'value': os.environ.get('ZYNTHIAN_UI_COLOR_PANEL_HL', "#2a323d"),
                'advanced': True
            },
            '_SPACER_': {
                'type': 'html',
                'content': "<br>",
            }
        }
        super().get("User Interface", config, errors)

    @tornado.web.authenticated
    def post(self):
        self.request.arguments['ZYNTHIAN_UI_SNAPSHOT_MIXER_SETTINGS'] = self.request.arguments.get(
            'ZYNTHIAN_UI_SNAPSHOT_MIXER_SETTINGS', '0')
        self.request.arguments['ZYNTHIAN_UI_RESTORE_LAST_STATE'] = self.request.arguments.get(
            'ZYNTHIAN_UI_RESTORE_LAST_STATE', '0')
        self.request.arguments['ZYNTHIAN_UI_PRESET_PRELOAD'] = self.request.arguments.get(
            'ZYNTHIAN_UI_PRESET_PRELOAD', '0')
        self.request.arguments['ZYNTHIAN_UI_ENABLE_CURSOR'] = self.request.arguments.get(
            'ZYNTHIAN_UI_ENABLE_CURSOR', '0')
        self.request.arguments['ZYNTHIAN_UI_TOUCH_NAVIGATION'] = self.request.arguments.get(
            'ZYNTHIAN_UI_TOUCH_NAVIGATION', '')
        self.request.arguments['ZYNTHIAN_VNCSERVER_ENABLED'] = self.request.arguments.get(
            'ZYNTHIAN_VNCSERVER_ENABLED', '0')
        escaped_arguments = tornado.escape.recursive_unicode(self.request.arguments)
        errors = self.update_config(escaped_arguments)
        self.restart_ui_flag = True
        self.get(errors)
