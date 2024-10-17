# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# Presets Manager Handler
#
# Copyright (C) 2020 Markus Heidt <markus@heidt-tech.com>
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
import copy
import glob
import shutil
import logging
import zipfile
import tarfile
import requests
import tornado.web

from zyngui.zynthian_gui_engine import *
from zyngine.zynthian_chain_manager import zynthian_chain_manager

from lib.upload_handler import TMP_DIR
from lib.zynthian_config_handler import ZynthianBasicHandler

# ------------------------------------------------------------------------------
# Soundfont Configuration
# ------------------------------------------------------------------------------


class PresetsConfigHandler(ZynthianBasicHandler):

    @tornado.web.authenticated
    def get(self):
        config = {
            'engines': self.get_engine_info(),
            'engine': self.get_argument('ENGINE', 'ZY'),
            'sel_node_id': self.get_argument('SEL_NODE_ID', -1),
            'musical_artifact_tags': self.get_argument('MUSICAL_ARTIFACT_TAGS', ''),
            'ZYNTHIAN_UPLOAD_MULTIPLE': True
        }
        super().get("presets.html", "Presets & Soundfonts", config, None)

    @tornado.web.authenticated
    def post(self, action):
        try:
            self.eng_code = self.get_argument('ENGINE', 'ZY')
            self.eng_info = self.get_engine_info()[self.eng_code]
            self.engine_cls = self.eng_info['ENGINE']
            if self.engine_cls == zynthian_engine_jalv:
                self.engine_cls.init_zynapi_instance(self.eng_code)
        except Exception as e:
            logging.error("Can't initialize engine '{}': {}\n{}".format(
                self.eng_code, e, self.eng_info))

        try:
            result = {
                'get_tree': lambda: self.do_get_tree(),
                'new_bank': lambda: self.do_new_bank(),
                'remove_bank': lambda: self.do_remove_bank(),
                'rename_bank': lambda: self.do_rename_bank(),
                'remove_preset': lambda: self.do_remove_preset(),
                'rename_preset': lambda: self.do_rename_preset(),
                'download': lambda: self.do_download(),
                'search': lambda: self.do_search(),
                'install': lambda: self.do_install_url(),
                'upload': lambda: self.do_install_file()
            }[action]()

        except:
            result = {}
        # JSON Ouput
        if result:
            self.write(result)

    def do_get_tree(self):
        result = {}
        try:
            result['methods'] = self.engine_cls.get_zynapi_methods()
            result['formats'] = self.get_upload_formats()
            result['presets'] = self.get_presets_data()
        except Exception as e:
            result['methods'] = None
            result['formats'] = None
            result['presets'] = None
            logging.error(e)
            result['errors'] = "Can't get preset tree data: {}".format(e)
        return result

    def do_new_bank(self):
        result = {}
        try:
            self.engine_cls.zynapi_new_bank(self.get_argument('NEW_BANK_NAME'))
        except Exception as e:
            logging.error(e)
            result['errors'] = "Can't create new bank: {}".format(e)
        result.update(self.do_get_tree())
        return result

    def do_rename_bank(self):
        result = {}
        try:
            self.engine_cls.zynapi_rename_bank(self.get_argument(
                'SEL_FULLPATH'), self.get_argument('SEL_BANK_NAME'))
        except Exception as e:
            logging.error(e)
            result['errors'] = "Can't rename bank: {}".format(e)
        result.update(self.do_get_tree())
        return result

    def do_remove_bank(self):
        result = {}
        try:
            self.engine_cls.zynapi_remove_bank(
                self.get_argument('SEL_FULLPATH'))
        except Exception as e:
            logging.error(e)
            result['errors'] = "Can't remove bank: {}".format(e)
        result.update(self.do_get_tree())
        return result

    def do_rename_preset(self):
        result = {}
        try:
            self.engine_cls.zynapi_rename_preset(self.get_argument(
                'SEL_FULLPATH'), self.get_argument('SEL_PRESET_NAME'))
        except Exception as e:
            logging.error(e)
            result['errors'] = "Can't rename preset: {}".format(e)
        result.update(self.do_get_tree())
        return result

    def do_remove_preset(self):
        result = {}
        try:
            self.engine_cls.zynapi_remove_preset(
                self.get_argument('SEL_FULLPATH'))
        except Exception as e:
            logging.error(e)
            result['errors'] = "Can't remove preset: {}".format(e)
        result.update(self.do_get_tree())
        return result

    def do_download(self):
        result = None
        fpath = None
        delete = False
        try:
            fpath = self.engine_cls.zynapi_download(
                self.get_argument('SEL_FULLPATH'))
            dname, fname = os.path.split(fpath)
            if os.path.isdir(fpath):
                zfpath = TMP_DIR + "/" + fname
                shutil.make_archive(zfpath, 'zip', fpath)
                fpath = zfpath + ".zip"
                fname += ".zip"
                delete = True
                mime_type = "application/zip"
            else:
                delete = False
                mime_type = "application/octet-stream"

            self.set_header('Content-Type', mime_type)
            self.set_header("Content-Description", "File Transfer")
            self.set_header('Content-Disposition',
                            'attachment; filename="{}"'.format(fname))
            with open(fpath, 'rb') as f:
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    self.write(data)
                self.finish()
        except Exception as e:
            logging.error(e)
            result = {
                "errors": "Can't download file: {}".format(e)
            }
        finally:
            if fpath and delete:
                os.remove(fpath)
        return result

    def do_search(self):
        result = {}
        try:
            maformats = self.engine_cls.zynapi_martifact_formats()
            result['search_results'] = self.search_artifacts(
                maformats, self.get_argument('MUSICAL_ARTIFACT_TAGS'))
        except OSError as e:
            logging.error(e)
            result['errors'] = "Can't search Musical Artifacts: {}".format(e)
        return result

    def do_install_file(self):
        result = {}
        try:
            for fpath in self.get_argument('INSTALL_FPATH').split(","):
                fpath = fpath.strip()
                if len(fpath) > 0:
                    self.install_file(fpath)
        except Exception as e:
            logging.error(e)
            result['errors'] = "Can't install file: {}".format(e)
        result.update(self.do_get_tree())
        return result

    def do_install_url(self):
        result = {}
        try:
            self.install_url(self.get_argument('INSTALL_URL'))
        except Exception as e:
            logging.error(e)
            result['errors'] = "Can't install URL: {}".format(e)
        result.update(self.do_get_tree())
        return result

    def search_artifacts(self, formats, tags):
        result = []
        for fmt in formats.split(','):
            query_url = "https://musical-artifacts.com/artifacts.json"
            sep = '?'
            if formats:
                query_url += sep + 'formats=' + fmt
                sep = "&"
            if tags:
                query_url += sep + 'tags=' + tags
                # query_url += sep + 'q=' + tags

            result += requests.get(query_url, verify=False).json()

        for row in result:
            if "file" not in row:
                if "mirrors" in row and len(row['mirrors']) > 0:
                    row['file'] = row['mirrors'][0]
                else:
                    row['file'] = None

        return result

    def install_file(self, fpath):
        logging.info("Unpacking '{}' ...".format(fpath))
        dpath = fpath
        try:
            if fpath.endswith('.tar.bz2'):
                dpath = fpath[:-8]
                tar = tarfile.open(fpath, "r:bz2")
                tar.extractall(dpath)
            elif fpath.endswith('.tar.gz'):
                dpath = fpath[:-7]
                tar = tarfile.open(fpath, "r:gz")
                tar.extractall(dpath)
            elif fpath.endswith('.tar.xz'):
                dpath = fpath[:-7]
                tar = tarfile.open(fpath, "r:xz")
                tar.extractall(dpath)
            elif fpath.endswith('.tgz'):
                dpath = fpath[:-4]
                tar = tarfile.open(fpath, "r:gz")
                tar.extractall(dpath)
            elif fpath.endswith('.zip'):
                dpath = fpath[:-4]
                with zipfile.ZipFile(fpath, 'r') as soundfontZip:
                    soundfontZip.extractall(dpath)

            if os.path.isdir(dpath):
                # Unroll nested dir
                head, tail = os.path.split(dpath)
                ddpath = f"{dpath}/{tail}"
                if os.path.isdir(ddpath):
                    # Rename subdir to avoid existing filename issues when moving up
                    tmp_subdir = dpath + "/zyn_tmp_subdir"
                    os.rename(ddpath, tmp_subdir)
                    # Move up nested dir content
                    for f in glob.glob(tmp_subdir + "/*"):
                        shutil.move(f, dpath)
                    # Remove empty nested dir
                    shutil.rmtree(tmp_subdir, ignore_errors=True)
                # Remove thrash ...
                shutil.rmtree(dpath + "/__MACOSX", ignore_errors=True)

            bank_fullpath = self.get_argument('SEL_BANK_FULLPATH')
            logging.info("Installing '{}' => '{}' ...".format(
                dpath, bank_fullpath))

            self.engine_cls.zynapi_install(dpath, bank_fullpath)

        # Always clean temporal files & dirs
        finally:
            try:
                os.remove(fpath)
            except:
                pass
            shutil.rmtree(dpath, ignore_errors=True)
            pass

    def install_url(self, url):
        logging.info("Downloading '{}' ...".format(url))
        res = requests.get(url, verify=False)
        head, tail = os.path.split(url)
        fpath = TMP_DIR + "/" + tail
        with open(fpath, "wb") as df:
            df.write(res.content)
            df.close()
            self.install_file(fpath)

    def get_engine_info(self):
        engine_info = copy.copy(zynthian_chain_manager.get_engine_info())
        for e in list(engine_info):
            if not engine_info[e]['ENABLED'] or not hasattr(engine_info[e]['ENGINE'], "zynapi_get_banks"):
                del engine_info[e]
        return engine_info

    def get_upload_formats(self):
        try:
            return self.engine_cls.zynapi_get_formats()
        except:
            return ""

    def get_presets_data(self):
        i = 0
        superbanks_data = []
        superbank_row = None
        banks_data = []
        try:
            for b in self.engine_cls.zynapi_get_banks():
                if b['fullpath'] is None:
                    if banks_data and superbank_row:
                        superbank_row['nodes'] = banks_data
                        superbanks_data.append(superbank_row)
                        banks_data = []
                    superbank_row = {
                        'id': i,
                        'text': b['text'],
                        'name': b['name'],
                        'fullpath': None,
                        'readonly': False,
                        'node_type': "BANK_HEAD",
                        'nodes': []
                    }
                    continue

                brow = {
                    'id': i,
                    'text': b['text'],
                    'name': b['name'],
                    'fullpath': b['fullpath'],
                    'readonly': b['readonly'],
                    'node_type': "BANK",
                    'nodes': [],
                    'icon': "glyphicon glyphicon-link" if b['readonly'] else None
                }
                i += 1
                try:
                    presets_data = []
                    for p in self.engine_cls.zynapi_get_presets(b):
                        prow = {
                            'id': i,
                            'text': p['text'],
                            'name': p['name'],
                            'fullpath': p['fullpath'],
                            'readonly': p['readonly'] or b['readonly'],
                            'bank_fullpath': b['fullpath'],
                            'node_type': 'PRESET',
                            'icon': "glyphicon glyphicon-link" if p['readonly'] else None
                        }
                        i += 1
                        presets_data.append(prow)

                    brow['nodes'] = presets_data

                except Exception as e:
                    logging.error("PRESET NODE {} => {}".format(i, e))

                banks_data.append(brow)

            if banks_data:
                if superbank_row:
                    superbank_row['nodes'] = banks_data
                    superbanks_data.append(superbank_row)
                else:
                    superbanks_data = banks_data

        except Exception as e:
            logging.error("BANK NODE {} => {}".format(i, e))

        return superbanks_data

# ------------------------------------------------------------------------------
