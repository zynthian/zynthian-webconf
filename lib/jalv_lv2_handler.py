# -*- coding: utf-8 -*-
#********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Presets Manager Handler
#
# Copyright (C) 2017 Markus Heidt <markus@heidt-tech.com>
#
#********************************************************************
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
#********************************************************************

import os
import logging
import tornado.web
import json
import lilv
from collections import OrderedDict
from lib.zynthian_config_handler import ZynthianConfigHandler


#------------------------------------------------------------------------------
# Jalv LV2 Configuration
#------------------------------------------------------------------------------

class JalvLv2Handler(ZynthianConfigHandler):
        JALV_LV2_CONFIG_FILE = "%s/jalv_plugins.json" % os.environ.get('ZYNTHIAN_CONFIG_DIR')

        all_plugins = None
        @tornado.web.authenticated
        def get(self, errors=None):
                config=OrderedDict([])
                if self.all_plugins is None:
                        self.load_all_plugins()

                config['ZYNTHIAN_JALV_PLUGINS'] = self.load_plugins()

                if self.genjson:
                        self.write(config)
                else:
                        if errors:
                                logging.error("Configuring JALV / LV2  failed: %s" % format(errors))
                                self.clear()
                                self.set_status(400)
                                self.finish("Configuring JALV / LV2  failed: %s" % format(errors))
                        else:
                                self.render("config.html", body="jalv_lv2.html", config=config, title="JALV / LV2 Plugins", errors=errors)

        @tornado.web.authenticated
        def post(self):
                action = self.get_argument('ZYNTHIAN_JALV_ACTION')
                if action:
                        errors = {
                                'INSTALL_LV2_PLUGINS': lambda: self.do_install_jalv()
                        }[action]()
                self.get(errors)


        def load_all_plugins(self):
                plugins = OrderedDict([])
                try:
                        world = lilv.World()
                        world.load_all()
                        for plugin in world.get_all_plugins():
                                if plugin.get_class().get_label()=="Generators":
                                        plugins[plugin.get_name(),{'URL': plugin.get_uri(), 'INSTALLED': False}]
                        self.all_plugins = OrderedDict(sorted(plugins.items()))
                except Exception as e:
                        logging.error('Loading list of all lv2 plugins failed: %s' % e)

        def load_plugins(self):
                result = self.all_plugins

                existing_plugins = self.load_installed_plugins();

                for plugin_name, plugin_properties in result.items():
                        if existing_plugins[plugin_name]:
                                plugin_properties['INSTALLED'] = True

                return result

        def load_installed_plugins(self):
                result = {}
                try:
                        with open(self.JALV_LV2_CONFIG_FILE) as f:
                                result = json.load(f)
                except Exception as e:
                        logging.info('Loading list of installed lv2 plugins failed: %s' % e)
                return result

        def do_install_jalv(self):

                try:
                        pluginJson = {}
                        self.load_all_plugins()
                        postedPlugins = tornado.escape.recursive_unicode(self.request.arguments)

                        for plugin_name, plugin_properties in self.all_plugins.items():
                                        if "ZYNTHIAN_JALV_INSTALL_%s" % plugin_name in postedPlugins:
                                                pluginJson[plugin_name] = plugin_properties['URL']

                        with open(self.JALV_LV2_CONFIG_FILE,'w') as f:
                                json.dump(pluginJson, f)

                except Exception as e:
                        logging.error("Installing jalv plugins failed: %s" % format(e))
                        return format(e)