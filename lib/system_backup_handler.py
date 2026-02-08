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
import json
import socket
import tornado.web
from io import BytesIO
from pathlib import Path
import subprocess
from subprocess import DEVNULL

from lib.zynthian_config_handler import ZynthianBasicHandler
from lib.zynthian_websocket_handler import ZynthianWebSocketMessageHandler, ZynthianWebSocketMessage


# ------------------------------------------------------------------------------
# Snapshot Config Handler
# ------------------------------------------------------------------------------
class SystemBackupHandler(ZynthianBasicHandler):

    CONFIG_BACKUP_ITEMS_FILE = "/zynthian/config/config_backup_items.txt"
    DATA_BACKUP_ITEMS_FILE = "/zynthian/config/data_backup_items.txt"
    CLOUD_BACKUP_CONFIG_FILE = "/zynthian/config/cloud_backup.json"
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

    def cloud_rsync_ssh_configured(self, username, server=None):
        # Return True if key installed on remote server and this zynthian can connect via ssh
        if server is None:
            # Our default / preferred cloud host is rsync.net who presents hostname same as username
            server = f"{username}.rsync.net"
        # Check host known
        if os.system(f"ssh-keygen -F {server}") != 0:
            return False
        return os.system(f"ssh \
                         -o BatchMode=yes \
                         -o PasswordAuthentication=no \
                         -o KbdInteractiveAuthentication=no \
                         -o ChallengeResponseAuthentication=no \
                         -o PreferredAuthentications=publickey \
                         -o ConnectTimeout=3 \
                         -t {username}@{server} ls > /dev/null") == 0

    def cloud_rsync_get_repos(self, username, server=None, path=None):
        # Returns list of kopia repositories
        if server is None:
            server = f"{username}.rsync.net"
        if path == None:
            # Default zynthian backup path on cloud storage is ~/zynthian/backup
            path = "zynthian/backup"
        result = subprocess.run(["ssh", f"{username}@{server}", "find", path, "-name", "kopia.repository*"], capture_output=True, text=True)
        repos = []
        for full_path in result.stdout.strip().splitlines():
            parts = full_path.split("/kopia.repository")
            if len(parts) < 2:
                continue
            try:
                repos.append(parts[0].split(f"{path}/")[1])
            except:
                pass
        return repos

    def cloud_get_uri(self):
        # Returns the uri that may be used to reconnect to the currently connected repo
        try:
            result = subprocess.run(["kopia", "repository", "status", "-t", "-s"], capture_output=True, text=True)
            return result.stdout.strip().split("$ kopia repository connect from-config --token ")[1].split('\n')[0]
        except:
            return None

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

        try:
            with open(self.CLOUD_BACKUP_CONFIG_FILE, "r") as f:
                config['CLOUD_CONFIG'] = json.load(f)
        except:
            config['CLOUD_CONFIG'] = {
                "username": "",
                "password": ""
            }
        username = config['CLOUD_CONFIG']["username"]
        config['CLOUD_CONFIG']['enabled'] = self.cloud_rsync_ssh_configured(username)
        config['CLOUD_CONFIG']['repos'] = self.cloud_rsync_get_repos(username)

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
                'BACKUP_ALL_CLOUD': lambda: self.do_cloud_backup("ALL"),
                'BACKUP_CONFIG_CLOUD': lambda: self.do_cloud_backup("CONFIG"),
                'BACKUP_DATA_CLOUD': lambda: self.do_cloud_backup("DATA"),
                'CLOUD_RESTORE_BACKUP_ALL': lambda: self.do_cloud_restore("ALL"),
                'CLOUD_RESTORE_BACKUP_CONFIG': lambda: self.do_cloud_restore("CONFIG"),
                'CLOUD_RESTORE_BACKUP_DATA': lambda: self.do_cloud_restore("DATA"),
                'CLOUD_RESTORE_NONE': lambda: self.do_cloud_restore(None),
                'SAVE_BACKUP_CONFIG': lambda: self.do_save_backup_config(),
                'SAVE_CLOUD_CONFIG': lambda: self.do_save_cloud_config()
            }[command]()

    def do_save_cloud_config(self):
        username = self.get_argument('CLOUD_USERNAME')
        password = self.get_argument('CLOUD_PASSWORD')
        server = self.get_argument('CLOUD_SERVER')
        if not server:
            server = f"{username}.rsync.net"

        # Check if ssh key installed on cloud server
        if not self.cloud_rsync_ssh_configured(username):
            # Update known_hosts file (ensures current config is correct)
            known_hosts_path = os.path.expanduser("~/.ssh/known_hosts")
            os.system(f"ssh-keygen -R {server} >> /dev/null 2>&1")
            os.system(f"ssh-keyscan -H {server} >> {known_hosts_path} 2>/dev/null")

            # Ensure RSA key is generated
            key_path = os.path.expanduser("~/.ssh/id_rsa")
            pub_key_path = f"{key_path}.pub"
            if not os.path.exists(pub_key_path):
                os.system(f"ssh-keygen -t rsa -b 4096 -f {key_path} -N")

            # Add zynthian ssh public key (download, manipulate and upload autorized_keys on remote host)
            ssh_password = self.get_argument('CLOUD_SSH_PASSWORD')
            os.system(f"sshpass -p {ssh_password} scp {username}@{server}:.ssh/authorized_keys /tmp/authkeys.0")
            os.system(f"cat {pub_key_path} /tmp/authkeys.0 | sort -u > /tmp/authkeys")
            os.system(f"sshpass -p {ssh_password} scp /tmp/authkeys {username}@{server}:.ssh/authorized_keys")
            os.system(f"rm /tmp/authkeys*")

        if self.cloud_rsync_ssh_configured(username):
            # Get list of existing repositories...
            repos = self.cloud_rsync_get_repos(username)
            hostname = socket.gethostname()
            if hostname in repos:
                # Connect to existing repo
                connected = os.system(f"kopia repository connect sftp --username {username} --host {server} --path zynthian/backup/{hostname} --keyfile $HOME/.ssh/id_rsa --known-hosts=$HOME/.ssh/known_hosts --password={password}") == 0
            else:
                # Create new repo
                connected = os.system(f"kopia repository create sftp --username {username} --host {server} --path zynthian/backup/{hostname} --keyfile $HOME/.ssh/id_rsa --known-hosts=$HOME/.ssh/known_hosts --password={password}")
            if connected:
                # Save cloud config
                with open(self.CLOUD_BACKUP_CONFIG_FILE, 'w') as f:
                    json.dump({"username": username, "password": password, "uri": self.cloud_get_uri()}, f)

        # Reload active tab
        active_tab = self.get_argument("ACTIVE_TAB", "BACKUP/RESTORE")
        self.do_get(active_tab)

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

    def do_cloud_backup(self, type):
        match(type):
            case "ALL":
                backup_items = self.get_all_backup_items()
            case "CONFIG":
                backup_items = self.get_config_backup_items()
            case "DATA":
                backup_items = self.get_data_backup_items()
            case _:
                backup_items = None
        if backup_items:
            with open(self.CLOUD_BACKUP_CONFIG_FILE, "r") as f:
                config = json.load(f)
            os.system(f"kopia repository connect from-config --token {config['uri']}")
            os.system(f"kopia snapshot create {' '.join(backup_items)}")
        # Reload active tab
        active_tab = self.get_argument("ACTIVE_TAB", "BACKUP/RESTORE")
        self.do_get(active_tab)

    def do_cloud_restore(self, type):
        match(type):
            case "ALL":
                backup_items = self.get_all_backup_items()
            case "CONFIG":
                backup_items = self.get_config_backup_items()
            case "DATA":
                backup_items = self.get_data_backup_items()
            case _:
                backup_items = None
        if backup_items:
            os.system(f"kopia snapshot restore {' '.join(backup_items)}")
        # Reload active tab
        active_tab = self.get_argument("ACTIVE_TAB", "BACKUP/RESTORE")
        self.do_get(active_tab)

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
