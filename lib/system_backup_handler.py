# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# System Backup Handler
#
# Copyright (C) 2017 Markus Heidt <markus@heidt-tech.com>
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
import time
import logging
import zipfile
import jsonpickle
import tornado.web
from io import BytesIO
from pathlib import Path

from lib.zynthian_config_handler import ZynthianBasicHandler
from lib.zynthian_websocket_handler import ZynthianWebSocketMessageHandler, ZynthianWebSocketMessage


# ------------------------------------------------------------------------------
# Snapshot Config Handler
# ------------------------------------------------------------------------------
class SystemBackupHandler(ZynthianBasicHandler):

    CONFIG_BACKUP_ITEMS_FILE = "/zynthian/config/config_backup_items.txt"
    DATA_BACKUP_ITEMS_FILE = "/zynthian/config/data_backup_items.txt"
    EXCLUDE_SUFFIX = ".exclude"

    @staticmethod
    def get_backup_items(filename):
        try:
            with open(filename) as f:
                return f.read().splitlines()
        except:
            return []

    @classmethod
    def get_config_backup_items(cls):
        return cls.get_backup_items(cls.CONFIG_BACKUP_ITEMS_FILE)

    @classmethod
    def get_data_backup_items(cls):
        return cls.get_backup_items(cls.DATA_BACKUP_ITEMS_FILE)

    @classmethod
    def get_all_backup_items(cls):
        res = cls.get_backup_items(cls.CONFIG_BACKUP_ITEMS_FILE)
        res += cls.get_backup_items(cls.DATA_BACKUP_ITEMS_FILE)
        return res

    @tornado.web.authenticated
    def get(self, errors=None):
        self.do_get("BACKUP/RESTORE", errors)

    def do_get(self, active_tab="BACKUP/RESTORE", errors=None):
        config = {
            'ACTIVE_TAB': active_tab,
            'ZYNTHIAN_UPLOAD_MULTIPLE': True,
            'CONFIG_BACKUP_ITEMS': {},
            'CONFIG_BACKUP_DIRS': [],
            'CONFIG_BACKUP_DIRS_EXCLUDED': [],
            'DATA_BACKUP_ITEMS': {},
            'DATA_BACKUP_DIRS': [],
            'DATA_BACKUP_DIRS_EXCLUDED': []
        }

        config_backup_items = self.get_config_backup_items()
        for item in config_backup_items:
            if item.startswith("^"):
                config['CONFIG_BACKUP_DIRS_EXCLUDED'].append(item[1:])
            else:
                config['CONFIG_BACKUP_DIRS'].append(item)

        data_backup_items = self.get_data_backup_items()
        for item in data_backup_items:
            if item.startswith("^"):
                config['DATA_BACKUP_DIRS_EXCLUDED'].append(item[1:])
            else:
                config['DATA_BACKUP_DIRS'].append(item)

        def add_config_backup_item(dirname, subdirs, files):
            if dirname not in config['CONFIG_BACKUP_ITEMS']:
                config['CONFIG_BACKUP_ITEMS'][dirname] = []
            for fname in files:
                config['CONFIG_BACKUP_ITEMS'][dirname].append(fname)

        def add_data_backup_item(dirname, subdirs, files):
            if dirname not in config['DATA_BACKUP_ITEMS']:
                config['DATA_BACKUP_ITEMS'][dirname] = []
            for fname in files:
                config['DATA_BACKUP_ITEMS'][dirname].append(fname)

        self.walk_backup_items(add_config_backup_item, config_backup_items)
        self.walk_backup_items(add_data_backup_item, data_backup_items)

        super().get("backup.html", "Backup / Restore", config, errors)

    @tornado.web.authenticated
    def post(self):
        command = self.get_argument('_command', '')
        logging.info("COMMAND = {}".format(command))
        if command:
            errors = {
                # 'RESTORE': pass,
                'BACKUP_ALL': lambda: self.do_backup_all(),
                'BACKUP_CONFIG': lambda: self.do_backup_config(),
                'BACKUP_DATA': lambda: self.do_backup_data(),
                'SAVE_BACKUP_CONFIG': lambda: self.do_save_backup_config()
            }[command]()

    def do_save_backup_config(self):
        # Save "Config" items
        backup_dirs = ''
        for dpath in self.get_argument('CONFIG_BACKUP_DIRS_EXCLUDED').split("\n"):
            if dpath:
                backup_dirs += "^{}\n".format(dpath)
        backup_dirs += self.get_argument('CONFIG_BACKUP_DIRS')
        with open(self.CONFIG_BACKUP_ITEMS_FILE, 'w') as backup_file:
            backup_file.write(backup_dirs)

        # Save "Data" items
        backup_dirs = ''
        for dpath in self.get_argument('DATA_BACKUP_DIRS_EXCLUDED').split("\n"):
            if dpath:
                backup_dirs += "^{}\n".format(dpath)
        backup_dirs += self.get_argument('DATA_BACKUP_DIRS')
        with open(self.DATA_BACKUP_ITEMS_FILE, 'w') as backup_file:
            backup_file.write(backup_dirs)

        # Reload active tab
        active_tab = self.get_argument("ACTIVE_TAB", "BACKUP/RESTORE")
        self.do_get(active_tab)

    def do_backup_all(self):
        backup_items = self.get_all_backup_items()
        self.do_backup('zynthian_backup', backup_items)

    def do_backup_config(self):
        backup_items = self.get_config_backup_items()
        self.do_backup('zynthian_config_backup', backup_items)

    def do_backup_data(self):
        backup_items = self.get_data_backup_items()
        self.do_backup('zynthian_data_backup', backup_items)

    def do_backup(self, fname_prefix, backup_items):
        zipname = '{0}{1}.zip'.format(
            fname_prefix, time.strftime("%Y%m%d-%H%M%S"))
        f = BytesIO()
        zf = zipfile.ZipFile(f, "w")

        def zip_backup_items(dirname, subdirs, files):
            logging.info(dirname)
            if dirname != '/':
                zf.write(dirname)
            for filename in files:
                logging.info(filename)
                zf.write(os.path.join(dirname, filename))

        self.walk_backup_items(zip_backup_items, backup_items)

        zf.close()
        self.set_header('Content-Type', 'application/zip')
        self.set_header('Content-Disposition',
                        'attachment; filename=%s' % zipname)

        self.write(f.getvalue())
        f.close()
        self.finish()

    def walk_backup_items(self, worker, backup_items):
        valitem_info = self.get_valitem_info(backup_items)
        for bdir in valitem_info["bdirs"]:
            for dirname, subdirs, files in os.walk(bdir):
                if not any(Path(dirname).match(xpat) for xpat in valitem_info["xpats"]):
                    worker(dirname, subdirs, files)

    @classmethod
    def get_valitem_info(cls, backup_items=None):
        xpats = []
        bdirs = []
        if not backup_items:
            backup_items = cls.get_all_backup_items()
        for bitem in backup_items:
            bitem = os.path.expandvars(bitem)
            if bitem.startswith("^"):
                xpats.append(bitem[1:])
            else:
                bdirs.append(bitem)
        return {
            "xpats": xpats,
            "bdirs": bdirs
        }


class RestoreMessageHandler(ZynthianWebSocketMessageHandler):

    @classmethod
    def is_registered_for(cls, handler_name):
        return handler_name == 'RestoreMessageHandler'

    def is_valid_restore_item(self, restore_item):
        restore_item = "/" + restore_item
        for xpat in self.valitem_info["xpats"]:
            if Path(restore_item).match(xpat):
                return False
        for bdir in self.valitem_info["bdirs"]:
            if str(restore_item).startswith(bdir):
                return True
        return False

    def on_websocket_message(self, restore_file):
        # fileinfo = self.request.files['ZYNTHIAN_RESTORE_FILE'][0]
        # restore_file = fileinfo['filename']
        with open(restore_file, "rb") as f:
            self.valitem_info = SystemBackupHandler.get_valitem_info()
            with zipfile.ZipFile(f, 'r') as restoreZip:
                for member in restoreZip.namelist():
                    if self.is_valid_restore_item(member):
                        log_message = "Restored: " + member
                        restoreZip.extract(member, "/")
                        logging.debug(log_message)
                        message = ZynthianWebSocketMessage(
                            'RestoreMessageHandler', log_message)
                        self.websocket.write_message(
                            jsonpickle.encode(message))
                    else:
                        logging.warning(
                            "Restore of " + member + " not allowed")
                restoreZip.close()
            f.close()
        os.remove(restore_file)
        SystemBackupHandler.update_sys()
        message = ZynthianWebSocketMessage(
            'RestoreMessageHandler', 'EOCOMMAND')
        self.websocket.write_message(jsonpickle.encode(message))
