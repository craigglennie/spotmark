import zmq
from zmq.eventloop import ioloop, zmqstream

DEFAULT_ZMQ_URI = "tcp://0.0.0.0:10000" 

class ZMQReceiver(object):
    """Reads messages from a ZeroMQ message stream. Uses
    tornado's event loop rather than repeatedly polling"""

    def __init__(self, msg_callback, zmq_uri=DEFAULT_ZMQ_URI):
        context = zmq.Context()
        self.pull_socket = context.socket(zmq.PULL)
        self.pull_socket.bind(zmq_uri)

        self.stream = zmqstream.ZMQStream(self.pull_socket)
        self.stream.on_recv(msg_callback)

    def setup_ioloop(self):
        ioloop.install()
        self.ioloop = ioloop.IOLoop.instance()

    def begin_receiving(self):
        """Start listening for messages"""
        self.setup_ioloop()
        self.ioloop.start()

class ZMQPeriodicReceiver(ZMQReceiver):
    """Like ZMQReceiver except that the callback is called at
    a user-specified interval"""
    
    def __init__(self, msg_callback, periodic_callback, periodic_callback_interval_ms, **kwargs):
        super(ZMQPeriodicReceiver, self).__init__(msg_callback, **kwargs)
        self.periodic_callback_interval_ms = periodic_callback_interval_ms 
        self.periodic_callback = periodic_callback

    def setup_ioloop(self):
        super(ZMQPeriodicReceiver, self).setup_ioloop()
        periodic = ioloop.PeriodicCallback(
            self.periodic_callback, self.periodic_callback_interval_ms, io_loop=self.ioloop
        )
        periodic.start()

class ZMQEmitter(object):
    """Class that knows how to send messages to a ZMQReceiver""" 

    def __init__(self, zmq_uri=DEFAULT_ZMQ_URI):
        context = zmq.Context()

        self.push_socket = context.socket(zmq.PUSH)
        self.push_socket.connect(zmq_uri)
    
    def __getattr__(self, name):
        """Expose the various send methods implement on the socket"""
        if "send" in name:
            return getattr(self.push_socket, name)
        return super(ZMQEmitter, self).__getattr__(name)
