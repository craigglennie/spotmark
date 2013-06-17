import accumulator
import ipc

def start():

    sqs_accumulator = accumulator.SQSAccumulator()
    streamer = ipc.ZMQPeriodicStreamer(
        sqs_accumulator.process_messages, 
        sqs_accumulator.enqueue_update,
         10000
    )

    sqs_accumulator.enqueue({"status": "running"})
    streamer.begin_streaming()

if __name__ == '__main__':
    start()

