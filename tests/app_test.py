from chalice.test import Client

def test_sns_handler():
    with Client(app) as client:
        response = client.lambda_.invoke(
            "foo",
            client.events.generate_sns_event(message="hello world")
        )
        assert response.payload == {'message': 'hello world'}
