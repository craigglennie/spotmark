import zmq
from zmq.eventloop import ioloop, zmqstream

DEFAULT_ZMQ_URI = "tcp://0.0.0.0:10000" 

class ZMQStreamer(object):
    """Reads messages from a ZeroMQ message stream. Uses
    tornado's event loop rather than repeatedly polling"""

    def __init__(self, msg_callback, zmq_uri=DEFAULT_ZMQ_URI):
        context = zmq.Context()
        pull_socket = context.socket(zmq.PULL)
        pull_socket.bind(zmq_uri)

        self.stream = zmqstream.ZMQStream(pull_socket)
        self.stream.on_recv(msg_callback)

    def setup_ioloop(self):
        ioloop.install()
        self.ioloop = ioloop.IOLoop.instance()

    def begin_streaming(self):
        """Start listening for messages"""

        self.setup_ioloop()
        self.ioloop.start()

class ZMQPeriodicStreamer(ZMQStreamer):
    """Like ZMQStreamer except that the callback is called at
    a user-specified interval"""
    
    def __init__(self, msg_callback, periodic_callback, periodic_callback_interval_ms, **kwargs):
        super(ZMQPeriodicStreamer, self).__init__(msg_callback, **kwargs)
        self.periodic_callback_interval_ms = periodic_callback_interval_ms 
        self.periodic_callback = periodic_callback

    def setup_ioloop(self):
        super(ZMQPeriodicStreamer, self).setup_ioloop()
        periodic = ioloop.PeriodicCallback(
            self.periodic_callback, self.periodic_callback_interval_ms, io_loop=self.ioloop
        )
        periodic.start()

class ZMQMessageSender(object):
    """Class that knows how to send messages to a ZMQStreamer""" 

    def __init__(self, zmq_uri=DEFAULT_ZMQ_URI):
        context = zmq.Context()

        self.push_socket = context.socket(zmq.PUSH)
        self.push_socket.connect(zmq_uri)
    
    def __getattr__(self, name):
        """Expose the various send methods implement on the socket"""
        if "send" in name:
            return getattr(self.push_socket, name)
        return super(ZMQMessageSender, self).__getattr__(name)
