from chalice.test import Client
from app import app


with open('example_sns_message.json', 'r') as file:
    message = file.read()

def test_sns_handler():
    with Client(app) as client:
        response = client.lambda_.invoke(
            "handle_sns_message",
            client.events.generate_sns_event(message=message)
        )
        assert response.payload == None
