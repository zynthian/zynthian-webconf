# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# System Backup Handler
#
# Copyright (C) 2017 Markus Heidt <markus@heidt-tech.com>
#               2026 Brian Walton <riban@zynthian.org>
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
import tarfile
import jsonpickle
import json
import socket
import tornado.web
import tempfile
import asyncio
from glob import glob
from pathlib import Path
import subprocess
from pathlib import PurePosixPath

from lib.zynthian_config_handler import ZynthianBasicHandler
from lib.zynthian_websocket_handler import ZynthianWebSocketMessageHandler, ZynthianWebSocketMessage


# ------------------------------------------------------------------------------
# Snapshot Config Handler
# ------------------------------------------------------------------------------

BACKUP_CONFIG_FILE = "/zynthian/config/backup.json"

class SystemBackupHandler(ZynthianBasicHandler):

    @staticmethod
    def save_config(config):
        try:
            with open(BACKUP_CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logging.warning(e)

    @staticmethod
    def get_config():
        try:
            with open(BACKUP_CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return SystemBackupHandler.get_legacy_config()

    @staticmethod
    def get_legacy_config():
        config = {
                "profile": None,
                "ZYNTHIAN_UPLOAD_MULTIPLE": True,
                "profiles":{
                    "Config": {
                        "paths": [
                            "${ZYNTHIAN_CONFIG_DIR}",
                            "/root/.config/Modartt",
                        ],
                        "exclude_paths": [],
                        "exclude_rules": []
                    },
                    "Data": {
                        "paths": [
                            "${ZYNTHIAN_MY_DATA_DIR}",
                            "/root/.local/share/Modartt"
                        ],
                        "exclude_paths": [],
                        "exclude_rules": []
                    }
                },
                "cloud": {}
            }
        for profile in ("Config", "Data"):
            try:
                with open(f"/zynthian/config/{profile.lower()}_backup_items.txt", "r") as f:
                    paths = f.readlines()
                root_paths = []
                exclude_paths = []
                for path in paths:
                    if path.startswith("^"):
                        exclude_paths.append(path[1:].strip())
                    else:
                        root_paths.append(path.strip())
                config["profiles"][profile]["paths"] = root_paths
                config["profiles"][profile]["exclude_paths"] = exclude_paths
            except:
                pass
        return config

    @tornado.web.authenticated
    def get(self, errors=None):
        self.do_get(errors=errors)

    def add_backup_item(dirname, subdirs, files):
        config = {dirname: []}
        for fname in files:
            config[dirname].append(fname)
        return config

    def do_get(self, errors=None):
        config = SystemBackupHandler.get_config()

        def expand_paths(paths):
            root_paths = set()
            root_paths.add("/")
            for path in paths:
                path = os.path.expandvars(path)
                parts = path.split("/")
                path = ""
                for part in parts:
                    if part:
                        path += f"/{part}"
                        root_paths.add(path)
            return root_paths

        def render_tree(node, exclude_paths, root_paths, disable, parent_checked=True):
            """ Create the html that represents the resolved files tree """
            html = "<ul>"
            if node["path"] in root_paths:
                checkbox = ""
            elif parent_checked and node["path"] not in exclude_paths:
                checkbox = f'<input type="checkbox" checked {disable}>'
            else:
                checkbox = f'<input type="checkbox" {disable}>'
                parent_checked = False
            html += f"""
            <li class="folder" data-path={node["path"]}>
                <span class="folder_icon">📂</span>
                {checkbox}
                {node['name']}
            """
            for f in node.get("files", []):
                path = f"{node['path']}/{f}"
                if path in root_paths:
                    checkbox = ""
                elif parent_checked and path not in exclude_paths:
                    checkbox = f'<input type="checkbox" checked {disable}>'
                else:
                    checkbox = f'<input type="checkbox" {disable}>'
                html += f"""
                <ul>
                    <li class="file" data-path={path}>
                        <span class="fileicon">📄</span>
                        {checkbox}
                        <span>{f}</span>
                    </li>
                </ul>
                """
            for child in node.get("dirs", {}).values():
                html += render_tree(child, exclude_paths, root_paths, disable, parent_checked)
            html += "</li></ul>"
            return html

        try:
            profile_name = config["profile"]
            if profile_name == "BACKUP_ALL":
                backup_items = {}
                for profile in config["profiles"].values():
                    backup_items.update(SystemBackupHandler.walk_backup_paths(profile["paths"]))
            else:
                profile = config["profiles"][profile_name]
                backup_items = SystemBackupHandler.walk_backup_paths(profile["paths"])

            # Build a tree of files and directories
            tree = {"name": "/", "dirs": {}, "files": [], "path": "/"}
            for dir_path, files in backup_items.items():
                parts = PurePosixPath(dir_path).parts
                if parts and parts[0] == "/":
                    parts = parts[1:]
                node = tree
                for part in parts:
                    node = node["dirs"].setdefault(part, {"name": part, "dirs": {}, "files": [], "path": dir_path})
                node["files"].extend(files)

            root_paths = expand_paths(profile["paths"])
            exclude_paths = expand_paths(profile["exclude_paths"])
            if profile_name == "BACKUP_ALL":
                disable = "disabled"
            else:
                disable = ""
            config['BACKUP_TREE'] = render_tree(tree, exclude_paths, root_paths, disable)
        except Exception as e:
            logging.warning(e)

        super().get("backup.html", "Backup / Restore", config, errors)

    @tornado.web.authenticated
    def post(self):
        command = self.get_argument('action', default=None)
        logging.info(f"COMMAND = {command}")
        if command:
            errors = {
                'SAVE_PROFILE': lambda: self.do_save_profile(),
            }[command]()
        else:
            self.do_set_profile()

    def do_set_profile(self):
        """ Update the selected profile using the html select """

        profile_name = self.get_argument("BACKUP_PROFILE", "BACKUP_ALL")
        config = SystemBackupHandler.get_config()
        config["profile"] = profile_name
        SystemBackupHandler.save_config(config)
        self.do_get()

    def do_save_profile(self):
        """ Save a profile to the configuration file """

        config = SystemBackupHandler.get_config()
        profile = self.get_argument("BACKUP_PROFILE")
        config["profiles"][profile]["paths"] = self.get_argument('BACKUP_PATHS').replace("\r", "").split("\n")
        config["profiles"][profile]["exclude_paths"] = self.get_argument('EXCLUDE_PATHS').replace("\r", "").split("\n")
        config["profiles"][profile]["exclude_rules"] = self.get_argument('EXCLUDE_RULES').replace("\r", "").split("\n")
        SystemBackupHandler.save_config(config)
        if config["cloud"]:
            for path in config["profiles"][profile]["paths"]:
                path = os.path.expandvars(path)
                rules = "\n".join(config["profiles"][profile]["exclude_rules"])
                for xpath in config["profiles"][profile]["exclude_paths"]:
                    if xpath.startswith(f"{path}/"):
                        xpath = xpath[len(path):]
                    rules += f"\n{xpath}"
                rules += "\n.kopiaignore"
                with open (f"{path}/.kopiaignore", "w") as f:
                    f.write(rules)

        self.do_get()


    @classmethod
    def walk_backup_paths(cls, backup_paths, exclude_paths=[], exclude_rules=[]):
        """ Get a dictionary of directory paths indexing a list of files within the directory
        Args:
            backup_paths: List of root paths to search (may include environmental variables)
            exclude_paths: List of paths (files and/or directories) to exclude
            exclude_rules: List of relative or absolute rules to exclude files or directories
        Returns: Dictionary: Lists of filenames, indexed by full directory paths
        """

        config = {}
        rules = []
        for rule in exclude_rules:
            rule = rule.strip()
            if rule.startswith("/"):
                # Absolute rule so add to exclude paths
                exclude_paths += glob(rule, root_dir="/")
            else:
                # Relative rule to be applied to each searched directory
                rules.append(rule)
        for item in backup_paths:
            item = os.path.expandvars(item)
            for dirname, subdirs, files in os.walk(item):
                local_exclude_paths = exclude_paths.copy()
                for rule in rules:
                    local_exclude_paths += glob(f"{dirname}/{rule}")
                files = [x for x in files if f"{dirname}/{x}" not in local_exclude_paths]
                if not any(Path(dirname).match(xpat) for xpat in local_exclude_paths):
                    config[dirname] = []
                    for fname in files:
                        config[dirname].append(fname)
        return config


    ### Cloud storage functions ###

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
        self.do_get()

class RestoreMessageHandler(ZynthianWebSocketMessageHandler):

    @classmethod
    def is_registered_for(cls, handler_name):
        return handler_name == 'RestoreMessageHandler'

    def on_websocket_message(self, restore_file):
        if restore_file == "kopia_backup":
            #os.system(f"kopia repository connect from-config --token {config['cloud']['uri']}")
            config = SystemBackupHandler.get_config()
            profile_name = config['profile']
            for path in config["profiles"][profile_name]["paths"]:
                path = os.path.expandvars(path)
                if not path:
                    continue
                cmd = ["kopia", "snapshot", "create", path, "--log-level=debug"]
                with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
                    for line in proc.stdout:
                        line = line.strip()
                        if line.startswith("snapshotted "):
                            result = json.loads(line.split('\t')[1])
                            message = ZynthianWebSocketMessage('RestoreMessageHandler', f"Backing up: {path}/{result['path']} ({result['files']} files)")
                            self.websocket.write_message(jsonpickle.encode(message))
            message = ZynthianWebSocketMessage('RestoreMessageHandler', 'EOCOMMAND')
            self.websocket.write_message(jsonpickle.encode(message))
            return
        elif restore_file == "kopia_restore":
            config = SystemBackupHandler.get_config()
            profile_name = config['profile']
            for path in config["profiles"][profile_name]["paths"]:
                path = os.path.expandvars(path)
                if not path:
                    continue
                cmd = ["kopia", "snapshot", "restore", path, "--log-level=debug"]
                with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
                    for line in proc.stdout:
                        line = line.strip()
                        if line.startswith("file"):
                            message = ZynthianWebSocketMessage('RestoreMessageHandler', f"Restored: {line[5:]}")
                            self.websocket.write_message(jsonpickle.encode(message))
            message = ZynthianWebSocketMessage('RestoreMessageHandler', 'EOCOMMAND')
            self.websocket.write_message(jsonpickle.encode(message))
            return
        elif restore_file.endswith("zip"):
            with open(restore_file, "rb") as f:
                with zipfile.ZipFile(f, 'r') as restoreZip:
                    for member in restoreZip.namelist():
                        log_message = "Restored: " + member
                        restoreZip.extract(member, "/")
                        logging.debug(log_message)
                        message = ZynthianWebSocketMessage('RestoreMessageHandler', log_message)
                        self.websocket.write_message(jsonpickle.encode(message))
                    restoreZip.close()
                f.close()
        else:
            # Open and extract the tar.gz file
            with tarfile.open(restore_file, "r:gz") as tar:
                for member in tar.getmembers():
                    tar.extract(member)
                    log_message = "Restored: " + member.name
                    logging.debug(log_message)
                    message = ZynthianWebSocketMessage(
                        'RestoreMessageHandler', log_message)
                    self.websocket.write_message(
                        jsonpickle.encode(message))
        os.remove(restore_file)
        SystemBackupHandler.update_sys()
        message = ZynthianWebSocketMessage(
            'RestoreMessageHandler', 'EOCOMMAND')
        self.websocket.write_message(jsonpickle.encode(message))
        
    async def restore_gzip(self):
        """Stream upload data and restore tar contents in real-time"""

        # Create a queue for streaming data from upload to tar extractor
        data_queue = asyncio.Queue(maxsize=10)
        loop = asyncio.get_event_loop()
        
        # Result storage
        results = {
            'success': True,
            'restored_files': [],
            'skipped_files': [],
            'errors': [],
            'total_size': 0
        }
        
        async def extract_tar():
            """Extract tar from queue data in background thread"""
            try:
                await loop.run_in_executor(
                    None,
                    self._extract_from_queue,
                    data_queue,
                    results
                )
            except Exception as e:
                print(f"Error in extractor: {e}")
                results['success'] = False
                results['errors'].append({'file': 'EXTRACTOR', 'error': str(e)})
        
        # Start extraction task
        extractor_task = asyncio.create_task(extract_tar())
        
        try:
            # Stream the request body to the queue
            bytes_received = 0
            async for chunk in self.request.connection.stream.read_until_close(streaming_callback=None):
                await data_queue.put(chunk)
                bytes_received += len(chunk)
                
                if bytes_received % (10 * 1024 * 1024) == 0:  # Log every 10MB
                    print(f"Received: {bytes_received / (1024*1024):.1f} MB")
            
            print(f"Upload complete: {bytes_received / (1024*1024):.1f} MB")
            
        except Exception as e:
            print(f"Error streaming upload: {e}")
            results['success'] = False
            results['errors'].append({'file': 'UPLOAD', 'error': str(e)})
        finally:
            # Signal end of stream
            await data_queue.put(None)
        
        # Wait for extraction to complete
        await extractor_task
        
        return results
    
    def _extract_from_queue(self, data_queue, restore_path, results):
        """Extract tar from streaming queue data (runs in thread pool)"""
        import io
        
        class QueueReader:
            """File-like object that reads from async queue"""
            def __init__(self, queue):
                self.queue = queue
                self.buffer = b''
                self.finished = False
                self.loop = asyncio.get_event_loop()
            
            def read(self, size=-1):
                """Read bytes from queue"""
                while not self.finished:
                    # If we have enough data, return it
                    if size > 0 and len(self.buffer) >= size:
                        data = self.buffer[:size]
                        self.buffer = self.buffer[size:]
                        return data
                    
                    # Get more data from queue
                    try:
                        future = asyncio.run_coroutine_threadsafe(
                            self.queue.get(),
                            self.loop
                        )
                        chunk = future.result(timeout=30)
                        
                        if chunk is None:
                            self.finished = True
                            break
                        
                        self.buffer += chunk
                        
                    except Exception as e:
                        print(f"Error reading from queue: {e}")
                        self.finished = True
                        break
                
                # Return whatever we have left
                if size > 0:
                    data = self.buffer[:size]
                    self.buffer = self.buffer[size:]
                    return data
                else:
                    data = self.buffer
                    self.buffer = b''
                    return data
            
            def readable(self):
                return True
            
            def seekable(self):
                return False
        
        try:
            # Create restore directory
            restore_dir = Path(restore_path)
            restore_dir.mkdir(parents=True, exist_ok=True)
            
            print("Opening tar stream...")
            
            # Create queue reader
            reader = QueueReader(data_queue)
            
            # Open tar from streaming data
            # Try different modes to auto-detect compression
            try:
                # First peek at data to detect compression
                peek_data = reader.read(3)
                reader.buffer = peek_data + reader.buffer
                
                if peek_data[:2] == b'\x1f\x8b':
                    mode = 'r|gz'  # Stream mode for gzip
                    print("Detected gzip compression")
                elif peek_data[:3] == b'BZh':
                    mode = 'r|bz2'
                    print("Detected bzip2 compression")
                else:
                    mode = 'r|'  # Stream mode for uncompressed
                    print("Detected uncompressed tar")
                
            except Exception:
                mode = 'r|gz'  # Default to gzip
            
            with tarfile.open(fileobj=reader, mode=mode) as tar:
                print("Extracting files...")
                
                for member in tar:
                    try:
                        # Build destination path
                        dest_path = restore_dir / member.name
                        
                        # Security check: prevent path traversal
                        if not str(dest_path.resolve()).startswith(str(restore_dir.resolve())):
                            results['errors'].append({
                                'file': member.name,
                                'error': 'Path traversal attempt detected'
                            })
                            continue

                        # Extract the member
                        tar.extract(member, path=restore_dir)
                        
                        # Record success
                        results['restored_files'].append({
                            'file': member.name,
                            'size': member.size,
                            'type': 'directory' if member.isdir() else 'file',
                            'path': str(dest_path)
                        })
                        results['total_size'] += member.size
                        
                        print(f"Restored: {member.name} ({member.size} bytes)")
                        
                    except Exception as e:
                        results['errors'].append({
                            'file': member.name,
                            'error': str(e)
                        })
                        print(f"Error restoring {member.name}: {e}")
            
            # Summary
            print(f"\nRestore complete:")
            print(f"  Restored: {len(results['restored_files'])} files")
            print(f"  Skipped: {len(results['skipped_files'])} files")
            print(f"  Errors: {len(results['errors'])} files")
            print(f"  Total size: {results['total_size'] / (1024*1024):.2f} MB")
            
            if results['errors']:
                results['success'] = False
            
        except Exception as e:
            results['success'] = False
            results['errors'].append({
                'file': 'GENERAL',
                'error': str(e)
            })
            print(f"General error during restore: {e}")
            import traceback
            traceback.print_exc()

class BackupDownloadHandler(tornado.web.RequestHandler):
    """Stream a tar.gz backup directly to the client without temp files."""

    async def get(self):
        config = SystemBackupHandler.get_config()
        profile_name = config["profile"]
        filename = f"zynthian_{profile_name.lower()}_backup{time.strftime('%Y%m%d-%H%M%S')}.tar.gz"
        profile = config["profiles"][profile_name]

        backup_tree = SystemBackupHandler.walk_backup_paths(
            profile["paths"], profile["exclude_paths"], profile["exclude_rules"]
        )
        paths = [f"{path}/{file}" for path, files in backup_tree.items() for file in files]

        self.set_header("Content-Type", "application/x-gz")
        self.set_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.set_header("Content-Encoding", "identity")
        self.set_header("Cache-Control", "no-cache")

        CHUNK = 512 * 1024
        loop = asyncio.get_event_loop()
        cancelled = False

        class QueueWriter:
            def __init__(self):
                self.queue = asyncio.Queue(maxsize=8)

            def write(self, data):
                if data:
                    future = asyncio.run_coroutine_threadsafe(
                        self.queue.put(data), loop
                    )
                    future.result(timeout=30)
                return len(data)

            def flush(self):
                pass  # tarfile calls this; nothing to do

            async def sentinel(self):
                """Signal end-of-stream."""
                await self.queue.put(None)

        writer = QueueWriter()

        def build_tar():
            try:
                with tarfile.open(fileobj=writer, mode="w:gz", compresslevel=1) as tar:
                    for path in paths:
                        if cancelled:
                            break
                        if os.path.exists(path):
                            try:
                                tar.add(path)
                            except Exception as e:
                                logging.warning(f"Skipping {path}: {e}")
            except Exception as e:
                logging.error(f"tar creation failed: {e}")
            finally:
                # Always post sentinel so the consumer can exit
                asyncio.run_coroutine_threadsafe(writer.sentinel(), loop).result(timeout=5)

        producer = loop.run_in_executor(None, build_tar)

        try:
            while True:
                chunk = await writer.queue.get()
                if chunk is None:          # sentinel → done
                    break
                self.write(chunk)
                await self.flush()
        except tornado.iostream.StreamClosedError:
            logging.warning("Client disconnected during backup download")
            cancelled = True
        except Exception as e:
            logging.error(f"Streaming error: {e}")
            cancelled = True
        finally:
            await producer   # wait for the thread to finish cleanly
            try:
                self.finish()
            except Exception:
                pass    
