import os
import requests

def get_metadata(data_name, default):
    if os.environ.get("SPOTMARK_ENVIRONMENT") != "AWS":
        return default
 
    response = requests.get(url)
    if not response.status_code == 200:
        error = "Non-200 response for %s: %s" % (url, response.content)
        raise AssertionError(error)
    return response.content

INSTANCE_ID = get_metadata("http://169.254.169.254/latest/meta-data/instance-id", "testing")

SQS_QUEUE_NAME = os.environ.get("SPOTMARK_SQS_QUEUE_NAME", "spotmark")
ZMQ_URI = os.environ.get("SPOTMARK_ZMQ_URI", "tcp://0.0.0.0:10000")
