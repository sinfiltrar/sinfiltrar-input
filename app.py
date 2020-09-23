from chalice import Chalice
import requests
import json
import boto3
import email

app = Chalice(app_name='sinfiltrar-input')
app.debug = True

url = 'https://search-sinfiltrar-input-y25ksi7pnwfkx6weatr6pfde24.us-west-2.es.amazonaws.com/main/_doc'

s3 = boto3.resource('s3', )

@app.route('/', methods=['POST'])
def index():
    request = app.current_request

    process_event(event)

@app.on_sns_message(topic='sinfiltrar-input')
def handle_sns_message(event):
    process_event(event)

def process_event(event):

    snsData = json.loads(event.message)
    app.log.debug("Received message with subject: %s, message: %s", event.subject, event.message)
    app.log.debug('SNS DATA %s', snsData['mail']['commonHeaders'])

    object = s3.Object(snsData['receipt']['action']['bucketName'], snsData['receipt']['action']['objectKey'])

    mailBody = object.get()['Body'].read().decode('utf-8')
    app.log.debug('Got body from %s/%s', snsData['receipt']['action']['bucketName'], snsData['receipt']['action']['objectKey'])

    parsedData = snsData['mail']['commonHeaders']

    emailObject = email.message_from_string(mailBody)

#     app.log.debug('parsedBody %s', parsedBody.__dict__)

    if emailObject.is_multipart():
      for part in emailObject.get_payload():
        app.log.debug('BODY %s', part.get_content_type())
        app.log(part)
    else:
      app.log.debug(emailObject.get_payload())

#     parsedData['body'] = mailBody

    r = requests.post(url, json = parsedData, headers = { 'Content-Type': 'application/json' })
    app.log.debug(r.status_code)
    app.log.debug(r.json())

