# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# DSP56300 emulator config
#
# Copyright (C) 2017-2024 Fernando Moyano <fernando@zynthian.org>
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
import glob
import shutil
import logging
import pexpect
import tornado.web
from subprocess import check_output, STDOUT

import zynconf
from lib.zynthian_config_handler import ZynthianBasicHandler
import zyngine.zynthian_lv2 as zynthian_lv2

# sys.path.append(os.environ.get('ZYNTHIAN_UI_DIR'))

# ------------------------------------------------------------------------------
# DSP56300 Emulator Configuration
# ------------------------------------------------------------------------------


class dsp56300Handler(ZynthianBasicHandler):
    data_dir = os.environ.get('ZYNTHIAN_DATA_DIR', "/zynthian/zynthian-data")
    my_data_dir = os.environ.get('ZYNTHIAN_MY_DATA_DIR', "/zynthian/zynthian-my-data")

    config_dpath = "/root/.local/share/The Usual Suspects"
    plugins_dpath = "/usr/local/lib/lv2"
    gear_info = {
        "Osirus": "http://theusualsuspects.lv2/Osirus",
        "OsTIrus": "http://theusualsuspects.lv2/OsTIrus",
        "Vavra": "http://theusualsuspects.lv2/Vavra",
        "Xenia": "http://theusualsuspects.lv2/Xenia",
        "JE8086": "http://theusualsuspects.lv2/JE8086"
    }

    @tornado.web.authenticated
    def get(self, errors=None):
        config = self.get_config()
        if errors:
            logging.error("DSP56300 Action Failed: %s" % format(errors))
        super().get("dsp56300.html", "DSP56300", config, errors)

    @tornado.web.authenticated
    def post(self):
        errors = None
        try:
            action = self.get_argument('ZYNTHIAN_DSP56300_ACTION')
        except:
            action = None
            logging.error(f"No action!")
        if action:
            try:
                errors = {
                    'INSTALL_OSIRUS_ROMFILE': lambda: self.do_install_romfile("Osirus"),
                    'INSTALL_OSTIRUS_ROMFILE': lambda: self.do_install_romfile("OsTIrus"),
                    'INSTALL_VAVRA_ROMFILE': lambda: self.do_install_romfile("Vavra"),
                    'INSTALL_XENIA_ROMFILE': lambda: self.do_install_romfile("Xenia"),
                    'DELETE_XENIA_ROMFILE': lambda: self.do_remove_romfile("Xenia"),
                }[action]()
            except Exception as err:
                logging.error(err)
        self.get(errors)

    def do_install_romfile(self, gear_name):
        plugin_bundle_dpath = self.plugins_dpath + "/" + gear_name + ".lv2"
        if not os.path.isdir(plugin_bundle_dpath):
            errors = f"Can't find a LV2 bundle dir for device '{gear_name}'"
            logging.error(errors)
            return errors

        gear_path = self.config_dpath + "/" + gear_name
        roms_dpath = gear_path + "/roms"
        if not os.path.isdir(roms_dpath):
            logging.info(f"Creating ROMs dir '{roms_dpath}'")
            os.makedirs(roms_dpath)

        try:
            plugin_uri = self.gear_info[gear_name]
        except:
            errors = f"Hardware Device '{gear_name}' is not supported"
            logging.error(errors)
            return errors

        fpath = self.get_argument(f"ZYNTHIAN_DSP56300_FILENAME")
        if fpath:
            logging.info(f"Installing ROM file {fpath} ...")
            try:
                # Remove existing ROM files
                logging.info(f"Remove existing ROM files from {plugin_bundle_dpath} ...")
                res = check_output(f"cd \"{plugin_bundle_dpath}\"; rm -f *.bin; rm -f *.BIN", shell=True, stderr=STDOUT).decode("utf-8")
                if gear_name != "Xenia":
                    logging.info(f"Remove existing ROM files from {roms_dpath} ...")
                    res = check_output(f"cd \"{roms_dpath}\"; rm -f *.bin; rm -f *.BIN; rm -f *.mid; rm -f *.MID", shell=True, stderr=STDOUT).decode("utf-8")
                # Copy uploaded file
                fname = os.path.basename(fpath)
                logging.info(f"Moving {fname} to {roms_dpath} ...")
                shutil.move(fpath, roms_dpath + "/" + fname)
                # Generate presets
                if gear_name in ("Osirus", "OsTIrus"):
                    errors = self.generate_presets(plugin_uri)
                # Copy patchmanager config file
                else:
                    pm_dpath = gear_path + "/patchmanager"
                    if not os.path.isdir(pm_dpath):
                        logging.info(f"Creating patchmanager config dir '{pm_dpath}'")
                        os.makedirs(pm_dpath)
                        check_output(f"cp -a \"{self.data_dir}/presets/{gear_name.lower()}/patchmanagerdb.json\" \"{pm_dpath}\"", shell=True, stderr=STDOUT)
            except Exception as e:
                errors = f"Install ROM file for '{gear_name}' failed: {e}"
                logging.error(errors)
        else:
            errors = 'Please, select a ROM file to install'

        return errors

    def do_remove_romfile(self, gear_name):
        roms_dpath = self.config_dpath + "/" + gear_name + "/roms"
        if not os.path.isdir(roms_dpath):
            errors = f"ROMs directory for '{gear_name}' doesn't exist!"
            logging.error(errors)
            return errors
        try:
            # Remove existing ROM files
            logging.info(f"Remove existing ROM files from {roms_dpath} ...")
            res = check_output(f"cd \"{roms_dpath}\"; rm -f *.bin; rm -f *.BIN; rm -f *.mid; rm -f *.MID", shell=True, stderr=STDOUT).decode("utf-8")
            errors = None
        except Exception as e:
            errors = f"Delete ROM files for '{gear_name}' failed: {e}"
            logging.error(errors)
        return errors

    def get_config(self):
        config = {
            'ZYNTHIAN_UPLOAD_MULTIPLE': False
        }
        for gname in self.gear_info:
            flist = self.get_rom_files(self.config_dpath + "/" + gname + "/roms")
            flist += self.get_rom_files(self.plugins_dpath + "/" + gname + ".lv2")
            if len(flist) > 0:
                config[f"ZYNTHIAN_DSP56300_ROM_FILE_{gname.upper()}"] = ", ".join(flist)
            else:
                config[f"ZYNTHIAN_DSP56300_ROM_FILE_{gname.upper()}"] = None
                logging.warning(f"No ROM files found for {gname}.")
        return config

    def get_rom_files(self, dpath):
        flist = list(glob.iglob("*.bin", root_dir=dpath)) + list(glob.iglob("*.BIN", root_dir=dpath))
        flist += list(glob.iglob("*.MID", root_dir=dpath)) + list(glob.iglob("*.mid", root_dir=dpath))
        return flist

    def generate_presets(self, plugin_uri):
        errors = None
        command = f"jalv -n dsp53600_webconf \"{plugin_uri}\""
        try:
            proc = pexpect.spawn(command, timeout=10)
            proc.delaybeforesend = 0
            proc.expect("\n> ")
            proc.terminate(True)
            res = check_output(f"regenerate_lv2_presets.sh {plugin_uri}", shell=True, stderr=STDOUT).decode("utf-8")
        except Exception as e:
            errors = f"Can't generate presets for '{plugin_uri}': {e}"
            logging.error(errors)
        return errors

# *****************************************************************************
