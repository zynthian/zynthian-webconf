# -*- coding: utf-8 -*-
# ********************************************************************
# ZYNTHIAN PROJECT: Zynthian Web Configurator
#
# SoundFont Manager Handler
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

import logging
import os.path
import shutil
import jsonpickle
import tornado.websocket
from tornadostreamform.multipart_streamer import MultiPartStreamer, TemporaryFileStreamedPart

from lib.zynthian_websocket_handler import ZynthianWebSocketMessageHandler, ZynthianWebSocketMessage

# ------------------------------------------------------------------------------
# Upload Handling
# ------------------------------------------------------------------------------

TMP_DIR = "/zynthian/zynthian-webconf/tmp"
if os.path.isdir(TMP_DIR):
    shutil.rmtree(TMP_DIR, ignore_errors=True)
os.mkdir(TMP_DIR)

MB = 1024 * 1024
GB = 1024 * MB
TB = 1024 * GB
MAX_STREAMED_SIZE = 1*TB


class UploadStreamPart(TemporaryFileStreamedPart):

    def move(self, file_path):
        if not self.is_finalized:
            raise Exception(
                "Cannot move temporary file: stream is not finalized yet.")
        if self.is_moved:
            raise Exception(
                "Cannot move temporary file: it has already been moved.")
        self.f_out.close()
        shutil.move(self.f_out.name, file_path)
        self.is_moved = True


class UploadPostDataStreamer(MultiPartStreamer):

    percent = 0

    def __init__(self, webSocketHandler, destinationPath, total):
        self.webSocketHandler = webSocketHandler
        self.destinationPath = destinationPath
        super().__init__(total)
        # super().__init__(total, tmp_dir=TMP_DIR)

    def create_part(self, headers):
        return UploadStreamPart(self, headers, tmp_dir=TMP_DIR)

    def on_progress(self, received, total):
        """Override this function to handle progress of receiving data."""
        if total:
            new_percent = received*100//total
            if new_percent != self.percent:
                self.percent = new_percent
                logging.debug(
                    f"Upload progress: {new_percent}, received: {received}, total: {total}")
                if self.webSocketHandler:
                    try:
                        message = ZynthianWebSocketMessage(
                            'UploadProgressHandler', str(new_percent))
                        self.webSocketHandler.websocket.write_message(
                            jsonpickle.encode(message))
                    except:
                        logging.warning(
                            f"Can't send upload progress to websocket: {new_percent}")

    def examine(self):
        print("============= structure =============")
        for idx, part in enumerate(self.parts):
            print("PART #", idx)
            print("    HEADERS")
            for header in part.headers:
                print("        ", repr(header.get("name", "")),
                      "=", repr(header.get("value", "")))
                params = header.get("params", None)
                if params:
                    for pname in params:
                        print("            ", repr(pname),
                              "=", repr(params[pname]))
            print("    DATA")
            print("        SIZE: ", part.get_size())
            print("        filename: ", part.get_filename())
            if part.get_size() < 80:
                print("        PAYLOAD:", repr(part.get_payload()))
            else:
                print("        PAYLOAD:", "<too long...>")

    def data_complete(self):
        super().data_complete()
        for part in self.parts:
            if part.get_size() > 0:
                destinationFilename = part.get_filename()
                logging.info(part.get_name())
                logging.info("destinationPath: " + self.destinationPath)
                part.move(self.destinationPath + "/" + destinationFilename)


class UploadProgressHandler(ZynthianWebSocketMessageHandler):
    clientId = '1'

    @classmethod
    def is_registered_for(cls, handler_name):
        return handler_name == 'UploadProgressHandler'

    def on_websocket_message(self, message):
        if message:
            self.clientId = message
        self.websocket.application.settings['upload_progress_handler'][self.clientId] = self
        # logging.info("progress handler set for %s" % self.clientId)

    # client disconnected
    def on_close(self):
        if self.clientId in self.websocket.application.settings['upload_progress_handler']:
            del self.websocket.application.settings['upload_progress_handler'][self.clientId]


@tornado.web.stream_request_body
class UploadHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        return self.get_secure_cookie("user")

    @tornado.web.authenticated
    def get(self, errors=None):
        # is not really used
        if self.ps and self.ps.percent:
            # logging.info("reporting percent: " + self.ps.percent)
            self.write(self.ps.percent)

    def post(self):
        try:
            # self.fout.close()
            self.ps.data_complete()
            # Use parts here!
            response = ''
            try:
                destinationPath = self.get_argument("destinationPath", TMP_DIR)
                part_files = []
                for part in self.ps.parts:
                    if part.get_size() > 0:
                        part_files.append(destinationPath +
                                          "/" + part.get_filename())

                response = ",".join(part_files)

            except Exception as e:
                logging.error("Copying uploaded files failed: %s" % e)

        finally:
            # Don't forget to release temporary files.
            self.ps.release_parts()
            self.write(response)
            self.finish

    def prepare(self):
        destinationPath = None
        try:
            global MAX_STREAMED_SIZE
            if self.request.method.lower() == "post":
                self.request.connection.set_max_body_size(MAX_STREAMED_SIZE)

            total = int(self.request.headers.get("Content-Length", "0"))
            client_id = self.get_argument("clientId")
            destinationPath = self.get_argument("destinationPath", TMP_DIR)
        except Exception as e:
            logging.error("prepare failed: %s" % e)
            total = 0
            client_id = '1'

        upload_progress_handler = None
        if client_id in self.application.settings['upload_progress_handler']:
            upload_progress_handler = self.application.settings['upload_progress_handler'][client_id]
        self.ps = UploadPostDataStreamer(
            upload_progress_handler,  destinationPath, total)

    def data_received(self, chunk):
        self.ps.data_received(chunk)
