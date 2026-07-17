# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Extra Packages handler
#
# Copyright (C) 2017-2026 Fernando Moyano <fernando@zynthian.org>
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
import sys
import time
import logging
import requests
import tornado.web
import urllib.parse
import oyaml as yaml
from pathlib import Path
from bs4 import BeautifulSoup
from subprocess import check_output, getoutput, STDOUT

from lib.zynthian_config_handler import ZynthianBasicHandler

# sys.path.append(os.environ.get('ZYNTHIAN_UI_DIR'))

# ------------------------------------------------------------------------------
# Extra Packages Handler
# ------------------------------------------------------------------------------


class ExtraPacksHandler(ZynthianBasicHandler):
    data_dir = os.environ.get('ZYNTHIAN_DATA_DIR', "/zynthian/zynthian-data")
    my_data_dir = os.environ.get('ZYNTHIAN_MY_DATA_DIR', "/zynthian/zynthian-my-data")
    packages_dir = os.environ.get('ZYNTHIAN_DIR', "/zynthian") + "/zynthian-packages"

    #package_cache_dpath = "/tmp/pack_info"
    #package_info_cache_fpath = self.package_cache_dpath + "/info.yml"
    package_info_cache_fpath = "/tmp/package_info.yml"

    download_url_base = "https://os.zynthian.org/packages"

    def prepare(self):
        super().prepare()
        force_reload = (self.request.headers.get("Cache-Control") == "no-cache")
        logging.debug(f"FORCE PACKAGE INFO RELOAD => {force_reload}")
        if force_reload or not self.get_cache_packages():
            self.get_packages()

    @tornado.web.authenticated
    def get(self, errors=None):
        if errors:
            logging.error("ERROR: %s" % format(errors))

        try:
            active_tab = self.get_argument('ZYNTHIAN_ACTIVE_TAB')
        except:
            active_tab = "Soundfonts"

        config = {
            'packs': self.pack_info,
            'ZYNTHIAN_ACTIVE_TAB': active_tab
        }
        super().get("extra_packs.html", "Packages", config, errors)

    @tornado.web.authenticated
    def post(self):
        errors = None
        try:
            install_pack_name = self.get_argument('ZYNTHIAN_EXTRAPACKS_INSTALL')
            uninstall_pack_name = self.get_argument('ZYNTHIAN_EXTRAPACKS_UNINSTALL')
        except:
            install_pack_name = None
            uninstall_pack_name = None
        if install_pack_name:
            try:
                errors = self.do_install_package(install_pack_name)
            except Exception as err:
                errors = f"Can't install package {install_pack_name}"
                logging.error(err)
        elif uninstall_pack_name:
            try:
                errors = self.do_uninstall_package(uninstall_pack_name)
            except Exception as err:
                errors = f"Can't uninstall package {uninstall_pack_name}"
                logging.error(err)
        self.get(errors)

    def get_pack_info(self, pack_name):
        for packs in self.pack_info.values():
            try:
                return packs[pack_name]
            except:
                pass

    def do_install_package(self, pack_name):
        errors = None
        try:
            info = self.get_pack_info(pack_name)
            if "pack_url" in info and info["pack_url"]:
                cmd = f"wget -q -O- \"{info['pack_url']}\" | tar -xJ -C \"{self.my_data_dir}/collections\""
                res = check_output(cmd, shell=True)
                if os.path.isdir(f"{self.my_data_dir}/collections/{pack_name}"):
                    info["installed"] = True
                    self.save_cache_packages()
                else:
                    raise Exception(f"Failed to download/unpack from '{info['pack_url']}'!")
            elif "pack_script" in info and info["pack_script"]:
                pack_script = info["pack_script"]
                res = getoutput(f"bash \"{pack_script}\" install")
                if getoutput(f"bash \"{pack_script}\" installed").split("\n")[0] == "installed":
                    info["installed"] = True
                    self.save_cache_packages()
                else:
                    raise Exception(f"Install script failed!")
        except Exception as e:
            errors = f"Error installing '{pack_name}' => {e}"
        if errors:
            logging.error(errors)
        else:
            self.restart_ui_flag = info['restart_ui']
        return errors

    def do_uninstall_package(self, pack_name):
        errors = None
        try:
            info = self.get_pack_info(pack_name)
            if "pack_url" in info and info["pack_url"]:
                cmd = f"rm -rf \"{self.my_data_dir}/collections/{pack_name}\""
                res = getoutput(cmd)
                if os.path.isdir(f"{self.my_data_dir}/collections/{pack_name}"):
                    raise Exception(f"Can't uninstall package!")
                else:
                    info["installed"] = False
                    self.save_cache_packages()
            elif "pack_script" in info and info["pack_script"]:
                pack_script = info["pack_script"]
                res = getoutput(f"bash \"{pack_script}\" uninstall")
                if getoutput(f"bash \"{pack_script}\" installed").split("\n")[0] == "installed":
                    raise Exception(f"Can't uninstall package!")
                else:
                    info["installed"] = False
                    self.save_cache_packages()
        except Exception as e:
            errors = f"Error uninstalling '{pack_name}' => {e}"
        if errors:
            logging.error(errors)
        else:
            self.restart_ui_flag = info['restart_ui']
        return errors

    def get_cache_packages(self):
        if os.path.isfile(self.package_info_cache_fpath):
            try:
                with open(self.package_info_cache_fpath, "r") as f:
                    yml = f.read()
                    self.pack_info = yaml.load(yml, Loader=yaml.SafeLoader)
                    return True
            except Exception as e:
                logging.error(e)
        return False

    def save_cache_packages(self):
        with open(self.package_info_cache_fpath, "w") as f:
             yaml.dump(self.pack_info, f)

    def get_packages(self):
        self.pack_info = {}
        for item in sorted(Path(self.packages_dir).iterdir()):
            if item.is_dir() and item.name[0] != '.':
                res = self.get_packages_from_cat(item)
                if res:
                    # Order packages by title
                    pack_list = sorted(res.values(), key=lambda p: p['title'])
                    pack_dict = {}
                    for p in pack_list:
                        pack_dict[p['name']] = p
                    self.pack_info[item.name] = pack_dict
        # Save package info cache
        self.save_cache_packages()

    def get_packages_from_cat(self, dpath):
        pack_info = {}

        for pack_dpath in dpath.iterdir():
            if not pack_dpath.is_dir():
                continue

            cat_name = dpath.name
            pack_name = pack_dpath.name

            # Ignore duplicates
            if pack_name in self.pack_info:
                continue

            # Get info from yaml file
            info_yml_fpath = f"{pack_dpath}/info.yml"
            try:
                with open(info_yml_fpath, "r", encoding="utf-8") as fd:
                    yml_info = yaml.safe_load(fd)
            except FileNotFoundError:
                logging.error(f"Can't find YAML file '{info_yml_fpath}'.")
            except yaml.YAMLError as exc:
                logging.error(f"Can't parse YAML file '{info_yml_fpath}' => {exc}")

            pack_base_url = f"{self.download_url_base}/{cat_name}/{pack_name}"

            # Check for a package script ...
            pack_script = Path(f"{pack_dpath}/{pack_name}.sh")
            if pack_script.is_file():
                if "size" in yml_info:
                    pack_size_text =  yml_info["size"]
                else:
                    pack_size_text =  "unknown"
                # Check if it's installed by running the package script
                installed = (getoutput(f"bash \"{pack_script}\" installed").split("\n")[0] == "installed")
                pack_url = None
            else:
                # No package script => Check existance of package file => Get package size
                pack_script = None
                pack_url = f"{pack_base_url}.tar.xz"
                try:
                    res = requests.head(pack_url)
                except Exception as e:
                    logging.error(e)
                if res.status_code == 200:
                    if "size" in yml_info:
                        # Trust size from info file
                        pack_size_text =  yml_info["size"]
                    else:
                        # Get size by querying package tar.xz file
                        pack_size = int(res.headers["content-length"])
                        if pack_size < 1000:
                            logging.error(f"Package file for '{pack_name}' is too small ({pack_size}).")
                            continue
                        pack_size = pack_size/(1000000)
                        if pack_size < 1000:
                            pack_size_text = f"{round(pack_size)}MB"
                        else:
                            pack_size_text = f"{pack_size/1000:.1f}GB"
                    # Check if it's installed by looking for the collection dir
                    installed = os.path.isdir(f"{self.my_data_dir}/collections/{pack_name}")
                else:
                    logging.error(f"Can't find package or script for '{pack_name}'!")
                    continue

            info = {
                "name": pack_name,
                "title": pack_name,
                "author": "unknown",
                "license": "unknown",
                "image": "",
                "description": "",
                "description_extended": "",
                "content": "miscelanea",
                "size": pack_size_text,
                "source_url": "",
                "pack_url": pack_url,
                "pack_script": pack_script,
                "restart_ui": False,
                "installed": installed
            }
            # Complete collection info
            if "title" in yml_info:
                info["title"] = yml_info["title"]
            if "author" in yml_info:
                info["author"] = yml_info["author"]
            if "license" in yml_info:
                info["license"] = yml_info["license"]
            if "description" in yml_info:
                parts = yml_info["description"].split("\n", 1)
                info["description"] = parts[0]
                if len(parts) > 1 and parts[1].strip():
                    ext_desc = parts[1].replace("\n", "</p><p>")
                    info["description_extended"] = f"<p>{ext_desc}</p>"
            if "source_url" in yml_info:
                info["source_url"] = yml_info["source_url"]
            if "icon" in yml_info:
                info["image"] = f"package_files/{cat_name}/{pack_name}/{yml_info['icon']}"
            if "content" in yml_info:
                info["content"] = yml_info['content']
            if "restart_ui" in yml_info:
                info["restart_ui"] = yml_info['restart_ui']
            # Add to the list
            pack_info[pack_name] = info

        return pack_info

# *****************************************************************************
