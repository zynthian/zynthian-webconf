import abc
import logging
import subprocess
import threading
from multiprocessing import Queue
import jsonpickle
import asyncio

from lib.zynthian_websocket_handler import ZynthianWebSocketMessage


class TailThread(threading.Thread):
    def __init__(self, websocket, loop, process_command):
        super(TailThread, self).__init__()
        self.is_logging = True
        self.websocket = websocket
        self.loop = loop
        self.process_command = process_command

    def stop(self):
        self.is_logging = False

    def run(self):
        process = subprocess.Popen(self.process_command, shell=True, stderr=subprocess.PIPE,
                                   stdout=subprocess.PIPE)

        stdout_queue = Queue()
        stdout_reader = AsynchronousFileReader(process.stdout, stdout_queue)
        stdout_reader.start()
        stderr_queue = Queue()
        stderr_reader = AsynchronousFileReader(process.stderr, stderr_queue)
        stderr_reader.start()
        asyncio.set_event_loop(self.loop)

        while self.is_logging and (not stdout_reader.eof() or not stderr_reader.eof()):
            while self.is_logging and not stdout_queue.empty() and not stdout_reader.eof():
                line = stdout_queue.get()
                logging.info("stdout: %s" % line.decode())

                message = ZynthianWebSocketMessage('UiLogMessageHandler', line.decode())
                self.websocket.write_message(jsonpickle.encode(message))
            while self.is_logging and not stderr_queue.empty() and not stderr_reader.eof():
                line = stderr_queue.get()
                logging.info("stderr: %s" %line.decode())

                message = ZynthianWebSocketMessage('UiLogMessageHandler', line.decode())
                self.websocket.write_message(jsonpickle.encode(message))

        stdout_reader.join()
        stderr_reader.join()
        process.stdout.close()
        process.stderr.close()

class AsynchronousFileReader(threading.Thread):
    '''
    Helper class to implement asynchronous reading of a file
    in a separate thread. Pushes read lines on a queue to
    be consumed in another thread.
    '''

    def __init__(self, fd, queue):
        assert callable(fd.readline)
        threading.Thread.__init__(self)
        self._fd = fd
        self._queue = queue

    def run(self):
        '''The body of the tread: read lines and put them on the queue.'''
        for line in iter(self._fd.readline, ''):
            self._queue.put(line)

    def eof(self):
        '''Check whether there is no more content to expect.'''
        return not self.is_alive() and self._queue.empty()