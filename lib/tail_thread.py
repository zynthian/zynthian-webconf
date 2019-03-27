import threading
import asyncio


class TailThread(threading.Thread):
    def __init__(self, websocket, loop):
        super(TailThread, self).__init__()
        self.is_running = True
        self.websocket = websocket
        asyncio.set_event_loop(loop)

    def stop(self):
        self.is_running = False


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
