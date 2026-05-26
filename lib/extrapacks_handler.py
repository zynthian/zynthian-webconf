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
from subprocess import check_output, getoutput, STDOUT

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

    def prepare(self):
        super().prepare()
        self.pack_info = self.get_remote_collections("https://os.zynthian.org/files/collections")
        self.pack_info.update(self.get_extra_packages())

    @tornado.web.authenticated
    def get(self, errors=None):
        if errors:
            logging.error("ERROR: %s" % format(errors))
        super().get("extra_packs.html", "Collections", { 'packs': self.pack_info }, errors)

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
            elif "pack_url" in info and info["pack_url"]:
                cmd = f"wget -q -O- \"{info['pack_url']}\" | tar -xJ -C \"{self.my_data_dir}/collections\""
                res = check_output(cmd, shell=True)
                if os.path.isdir(f"{self.my_data_dir}/collections/{pack_name}"):
                    info["installed"] = True
                else:
                    raise(f"Can't install package file!")
            elif "pack_script" in info and info["pack_script"]:
                pack_script = info["pack_script"]
                res = getoutput(f"bash \"{pack_script}\" install")
                if getoutput(f"bash \"{pack_script}\" installed").split("\n")[0] == "installed":
                    info["installed"] = True
                else:
                    raise(f"Can't install package!")
        except Exception as e:
            errors = f"Error installing '{pack_name}' => {e}"
        if errors:
            logging.error(errors)
        return errors

    def do_uninstall_package(self, pack_name):
        errors = None
        try:
            info = self.pack_info[pack_name]
            if "pack_url" in info and info["pack_url"]:
                cmd = f"rm -rf \"{self.my_data_dir}/collections/{pack_name}\""
                res = getoutput(cmd)
                if os.path.isdir(f"{self.my_data_dir}/collections/{pack_name}"):
                    raise(f"Can't uninstall package!")
                else:
                    info["installed"] = False
            elif "pack_script" in info and info["pack_script"]:
                pack_script = info["pack_script"]
                res = getoutput(f"bash \"{pack_script}\" uninstall")
                if getoutput(f"bash \"{pack_script}\" installed").split("\n")[0] == "installed":
                    raise(f"Can't uninstall package!")
                else:
                    info["installed"] = False
        except Exception as e:
            errors = f"Error uninstalling '{pack_name}' => {e}"
        if errors:
            logging.error(errors)
        return errors

    def get_remote_collections(self, url):
        col_info = {}
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

                # Ignore theme folder
                if col_name == "theme":
                    continue

                # Get info from yaml file
                try:
                    yml = requests.get(f"{col_url}/info.yml").text
                except:
                    logging.debug(f"Can't find info file for collection '{col_url}'")
                    continue
                # Parse yaml info
                try:
                    pack_info = yaml.load(yml, Loader=yaml.SafeLoader)
                except Exception as e:
                    logging.debug(f"Can't parse yaml info file for collection '{col_url}' => {e}")
                    continue

                try:
                    # Check for a package script ...
                    res = requests.get(f"{col_url}/{col_name}.sh").text
                    if res:
                        pack_script = f"/tmp/{col_name}.sh"
                        with open(pack_script, "w") as f:
                            f.write(res)
                    else:
                        raise f"Package script not available for {col_name}!"
                    if "size" in pack_info:
                        pack_size_text =  pack_info["size"]
                    # Check if it's installed by running the package script
                    installed = (getoutput(f"bash \"{pack_script}\" installed").split("\n")[0] == "installed")
                    pack_url = None
                except:
                    # No package script => Check existance of package file => Get package size
                    pack_script = None
                    pack_url = f"{col_url}/{col_name}.tar.xz"
                    res = requests.head(pack_url)
                    pack_size = int(res.headers["content-length"])
                    if pack_size < 1000:
                        logging.debug(f"Can't find package or script for '{col_name}'")
                        continue
                    pack_size = pack_size/(1000000)
                    if pack_size < 1000:
                        pack_size_text = f"{round(pack_size)}MB"
                    else:
                        pack_size_text = f"{pack_size/1000:.1f}GB"
                    # Check if it's installed by looking for the collection dir
                    installed = os.path.isdir(f"{self.my_data_dir}/collections/{col_name}")

                info = {
                    "title": col_name,
                    "author": "Unknown",
                    "license": "Unknown",
                    "image": "",
                    "description": "",
                    "content": "miscelanea",
                    "size": pack_size_text,
                    "source_url": "",
                    "pack_url": pack_url,
                    "pack_script": pack_script,
                    "restart_ui_flag": False,
                    "installed": installed
                }
                # Complete collection info
                if "author" in pack_info:
                    info["author"] = pack_info["author"]
                if "license" in pack_info:
                    info["license"] = pack_info["license"]
                if "description" in pack_info:
                    description = "<p>" + pack_info["description"].replace("\n", "</p><p>") + "</p>"
                    info["description"] = description
                if "source_url" in pack_info:
                    info["source_url"] = pack_info["source_url"]
                if "icon" in pack_info:
                    info["image"] = f"{col_url}/{pack_info['icon']}"
                if "content" in pack_info:
                    info["content"] = pack_info['content']
                # Add to the list
                col_info[col_name] = info
        return col_info

    def get_extra_packages(self):
        extra_pack_info = {
            "IR_Collection": {
                "title": "IR Collection",
                "author": "Various",
                "license": "Free (Various)",
                "image": "",
                "content": "IRs",
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
                "content": "IRs",
                "description": "<p>A collection of impulse response files that you can load with the X42's IR convolver plugins and others. A huge collection of well organized, experimental IRs, under MIT license. It will surprise you.</p>",
                "size": "650MB",
                "source_url": "https://github.com/itsmusician/IR-Library",
                "recipe": "install_Conners_IR_library.sh",
                "restart_ui_flag": False,
                "installed": False
            }
        }

        # Check if IR_collection is installed
        subpacks = ["ccgb", "jezwells", "l480", "openairlib", "samplicity-m7", "teufelsberg"]
        res = True
        for subpack in subpacks:
            if not os.path.islink(f"{self.data_dir}/files/IRs/{subpack}"):
                res = False
                break
        extra_pack_info['IR_Collection']['installed'] = res

        # Check if Conners_IR_library is installed
        if os.path.isdir(f"{self.data_dir}/files/IRs/Conners"):
            res = True
        else:
            res = False
        extra_pack_info['Conners_IR_library']['installed'] = res

        # Return dictionary
        return extra_pack_info

# *****************************************************************************
