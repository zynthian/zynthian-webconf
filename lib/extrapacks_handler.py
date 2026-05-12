# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Extra Packages handler
#
# Copyright (C) 2017-2025 Fernando Moyano <fernando@zynthian.org>
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
import logging
import requests
import tornado.web
import urllib.parse
import oyaml as yaml
from bs4 import BeautifulSoup
from subprocess import check_output, STDOUT

import zynconf
from lib.zynthian_config_handler import ZynthianBasicHandler
import zyngine.zynthian_lv2 as zynthian_lv2

# sys.path.append(os.environ.get('ZYNTHIAN_UI_DIR'))

# ------------------------------------------------------------------------------
# Extra Packages Handler
# ------------------------------------------------------------------------------


class ExtraPacksHandler(ZynthianBasicHandler):
    data_dir = os.environ.get('ZYNTHIAN_DATA_DIR', "/zynthian/zynthian-data")
    my_data_dir = os.environ.get('ZYNTHIAN_MY_DATA_DIR', "/zynthian/zynthian-my-data")

    pack_info = {
        "Hydrogen_Drumkits": {
            "title": "Hydrogen Drumkits",
            "author": "Various",
            "license": "Free (Various)",
            "image": "",
            "description": "<p>A collection of drumkits, using the Hydrogen format, that you can load with Fabla and DrMr sampler.</p>`",
            "size": "145MB",
            "source_url": "https://musical-artifacts.com/artifacts/133",
            "recipe": "install_hydrogen_drumkits.sh",
            "restart_ui_flag": True,
            "installed": False
        },
        "IR_Collection": {
            "title": "IR Collection",
            "author": "Various",
            "license": "Free (Various)",
            "image": "",
            "description": "<p>A collection of impulse response files that you can load with the X42's IR convolver plugins and others. It includes several free IR libraries: ccgb, jezwells, l480, openairlib, samplicity-m7 and teufelsberg.</p>",
            "size": "245MB",
            "source_url": "",
            "recipe": "install_ir-lv2-presets.sh",
            "restart_ui_flag": False,
            "installed": False
        },
        "Conners_IR_library": {
            "title": "Conners IR library",
            "author": "Conners",
            "license": "MIT",
            "image": "",
            "description": "<p>A collection of impulse response files that you can load with the X42's IR convolver plugins and others. A huge collection of well organized, experimental IRs, under MIT license. It will surprise you.</p>",
            "size": "650MB",
            "source_url": "https://github.com/itsmusician/IR-Library",
            "recipe": "install_Conners_IR_library.sh",
            "restart_ui_flag": False,
            "installed": False
        }
    }

    @tornado.web.authenticated
    def get(self, errors=None):
        self.get_remote_collections("https://os.zynthian.org/files/collections")
        self.get_installed_info()
        if errors:
            logging.error("ERROR: %s" % format(errors))
        super().get("extra_packs.html", "Extra Packages", { 'packs': self.pack_info }, errors)

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
                self.restart_ui_flag = self.pack_info[install_pack_name]['restart_ui_flag']
            except Exception as err:
                errors = f"Can't install package {install_pack_name}"
                logging.error(err)
        elif uninstall_pack_name:
            try:
                errors = self.do_uninstall_package(uninstall_pack_name)
                self.restart_ui_flag = self.pack_info[uninstall_pack_name]['restart_ui_flag']
            except Exception as err:
                errors = f"Can't uninstall package {uninstall_pack_name}"
                logging.error(err)
        self.get(errors)

    def do_install_package(self, pack_name):
        errors = None
        try:
            info = self.pack_info[pack_name]
            if "recipe" in info:
                res = check_output(f"$ZYNTHIAN_RECIPE_DIR/{info['recipe']}", shell=True)
            elif "collection_url" in info:
                cmd = f"wget -q -O- \"{info['collection_url']}\" | tar -xJ -C \"{self.my_data_dir}/collections\""
                res = check_output(cmd, shell=True)
                if not os.path.isdir(f"{self.my_data_dir}/collections/{pack_name}"):
                    raise(f"Can't install package file!")
        except Exception as e:
            errors = f"Error installing '{pack_name}' => {e}"
        if errors:
            logging.error(errors)
        return errors

    def do_uninstall_package(self, pack_name):
        errors = None
        try:
            info = self.pack_info[pack_name]
            if "collection_url" in info:
                cmd = f"rm -rf \"{self.my_data_dir}/collections/{pack_name}\""
                res = check_output(cmd, shell=True)
                if os.path.isdir(f"{self.my_data_dir}/collections/{pack_name}"):
                    raise(f"Can't uninstall package!")
        except Exception as e:
            errors = f"Error uninstalling '{pack_name}' => {e}"
        if errors:
            logging.error(errors)
        return errors

    def get_remote_collections(self, url):
        try:
            page = requests.get(url).text
        except:
            return
        soup = BeautifulSoup(page, 'html.parser')
        for node in soup.find_all("a")[::-1]:
            href = urllib.parse.unquote(node.get('href'))
            if href[-1] == "/":
                href = href[:-1]
            if not href.startswith("http") and href[0] not in ("/", "?"):
                # It's a collection dir =>
                col_name = href
                col_url = f"{url}/{col_name}"
                # Get package size
                pack_url = f"{col_url}/{col_name}.tar.xz"
                try:
                    res = requests.head(pack_url)
                    pack_size = int(res.headers["content-length"])
                    if pack_size < 1000:
                        logging.debug(f"Package '{pack_url}' not available!")
                        continue
                except Exception as e:
                    logging.debug(f"Can't get info for collection package '{pack_url}' => {e}")
                    continue
                info = {
                    "title": col_name,
                    "author": "Unknown",
                    "license": "Unknown",
                    "image": "",
                    "description": "",
                    "size": f"{round(pack_size//(1024*1024))}MB",
                    "source_url": "",
                    "pack_url": pack_url,
                    "restart_ui_flag": False,
                    "installed": False
                }
                # Get info from yaml file
                try:
                    yml = requests.get(f"{col_url}/info.yml").text
                except:
                    logging.debug(f"Can't find info file for collection '{col_url}'")
                    continue
                # Parse yaml info
                try:
                    col_info = yaml.load(yml, Loader=yaml.SafeLoader)
                except Exception as e:
                    logging.debug(f"Can't parse yaml info file for collection '{col_url}' => {e}")
                    continue
                # Complete collection info
                if "author" in col_info:
                    info["author"] = col_info["author"]
                if "license" in col_info:
                    info["license"] = col_info["license"]
                if "description" in col_info:
                    description = "<p>" + col_info["description"].replace("\n", "</p><p>") + "</p>"
                    info["description"] = description
                if "source_url" in col_info:
                    info["source_url"] = col_info["source_url"]
                if "icon" in col_info:
                    info["image"] = f"{col_url}/{col_info['icon']}"
                # Add to the list
                self.pack_info[col_name] = info

    def get_installed_info(self):
        # Check if Hydrogen_Drumkits is installed
        drumkits = ["3355606kit", "Audiophob", "circAfrique v4", "Drumkit excepcional", "ElectricEmpireKit"]
        res = True
        for drumkit in drumkits:
            if not os.path.isdir(f"{self.data_dir}/soundfonts/hydrogen/{drumkit}"):
                res = False
                break
        self.pack_info['Hydrogen_Drumkits']['installed'] = res

        # Check if IR_collection is installed
        subpacks = ["ccgb", "jezwells", "l480", "openairlib", "samplicity-m7", "teufelsberg"]
        res = True
        for subpack in subpacks:
            if not os.path.islink(f"{self.data_dir}/files/IRs/{subpack}"):
                res = False
                break
        self.pack_info['IR_Collection']['installed'] = res

        # Check if Conners_IR_library is installed
        if os.path.isdir(f"{self.data_dir}/files/IRs/Conners"):
            res = True
        else:
            res = False
        self.pack_info['Conners_IR_library']['installed'] = res

        for pack_name, info in self.pack_info.items():
            if "pack_url" in info:
                if os.path.isdir(f"{self.my_data_dir}/collections/{pack_name}"):
                    res = True
                else:
                    res = False
                self.pack_info[pack_name]['installed'] = res



# *****************************************************************************
