import multiprocessing
import unittest
import time

from spotmark import ipc

class EmitterProcess(multiprocessing.Process):
    
    def __init__(self, id, num_messages):
        super(EmitterProcess, self).__init__()
        self.id = id
        self.num_messages = num_messages

    def run(self):
        # Instantiaing the emitter in the constructor causes problems
        # because you can't create a context, then fork, and then use
        # the context - ZMQ will die
        zmq_emitter = ipc.ZMQEmitter()
        sent = 0
        while sent < self.num_messages:
            zmq_emitter.send_string(str(self.id))
            sent += 1

class ReceiverProcess(multiprocessing.Process):

    def __init__(self, queue):
        super(ReceiverProcess, self).__init__(args=(queue,))
        
    def messages_received(self, messages):
        queue = self._args[0]
        queue.put(messages)

    def run(self):
        receiver = ipc.ZMQReceiver(self.messages_received)
        receiver.begin_receiving()        

class TestIPC(unittest.TestCase):
    """Integration tests for fan-in messaging with ZeroMQ.

    Creates a number of emitter processes all sending messages to a single
    receiver process. Receiver process requeues these messages for the test
    class to process."""

    def setUp(self):
        super(TestIPC, self).setUp()
        self.messages = []
        self.queue = multiprocessing.Queue()
        self.receiver = ReceiverProcess(self.queue)

        self.num_messages = 5
        self.emitters = [EmitterProcess(i, self.num_messages) for i in range(5)]

    def tearDown(self):
        self.receiver.terminate()        
        for emitter in self.emitters:
            emitter.terminate()

    def test_ipc(self):

        self.receiver.start()

        for emitter in self.emitters:
            emitter.start()

        wait_seconds = 10
        start = time.time()
        message_count = 0
        while 1:
            messages = self.queue.get(timeout=wait_seconds)
            if messages:
                message_count += len(messages)
            if message_count == self.num_messages * len(self.emitters):
                break


