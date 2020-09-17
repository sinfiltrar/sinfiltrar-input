from chalice import Chalice
import requests
import json
import boto3

app = Chalice(app_name='sinfiltrar-input')
app.debug = True

url = 'https://search-sinfiltrar-input-y25ksi7pnwfkx6weatr6pfde24.us-west-2.es.amazonaws.com/main/_doc'

s3 = boto3.resource('s3', )

@app.on_sns_message(topic='sinfiltrar-input')
def handle_sns_message(event):

    snsData = json.loads(event.message)
    app.log.debug("Received message with subject: %s, message: %s", event.subject, event.message)

    app.log.debug('SNS DATA %s', snsData)

    object = s3.Object(data['receipt']['action']['bucketName'], data['receipt']['action']['objectKey'])
    app.log.debug('Got body from %s', data['receipt'])

    mailBody = object.get()['Body'].read().decode('utf-8')

    parsedData = {
        "from":
        "to":
        "subject":
        "body":
    }


    r = requests.post(url, json = parsedData, headers = { 'Content-Type': 'application/json' })
    app.log.debug(r.status_code)
    app.log.debug(r.json())
