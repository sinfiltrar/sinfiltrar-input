from chalice.test import Client
from app import app
import json


def test_email_1():
    payload = sns_handler_test('tgc9bleng0asjn49k6u2336kn9dh6838siljg1g1')
    assert payload == None

def test_email_2():
    payload = sns_handler_test('igifg6nk4gvu27enf2rqng6217ka1h8qa8lbj1o1')
    assert payload == None

def sns_handler_test(object, bucket = 'sinfiltrar-input'):

    message = {
        "receipt": {
            "action": {
                "bucketName": bucket,
                "objectKey": object
            }
        }
    }

    with Client(app) as client:
        response = client.lambda_.invoke(
            "handle_sns_message",
            client.events.generate_sns_event(message=json.dumps(message))
        )

        return response.payload
