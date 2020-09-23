from chalice import Chalice
import requests
import json
import boto3
import email

app = Chalice(app_name='sinfiltrar-input')
app.debug = True

url = 'https://search-sinfiltrar-input-y25ksi7pnwfkx6weatr6pfde24.us-west-2.es.amazonaws.com/main/_doc'

s3 = boto3.resource('s3', )

s3client = boto3.client('s3')

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


    app.log.debug('Downloading from %s/%s', snsData['receipt']['action']['bucketName'], snsData['receipt']['action']['objectKey'])
    mailBody = object.get()['Body'].read().decode('utf-8')
    app.log.debug('Got body from %s/%s', snsData['receipt']['action']['bucketName'], snsData['receipt']['action']['objectKey'])

    parsedData = snsData['mail']['commonHeaders']

    emailObject = email.message_from_string(mailBody)

#     app.log.debug('parsedBody %s', parsedBody.__dict__)

    parsedData['attachments'] = []

#     parsedData['body_plain'] = emailObject.get_body(('plain', ))
#     parsedData['body'] = emailObject.get_body(('related', 'html', 'plain'))

    if emailObject.is_multipart():
        for i, att in enumerate(emailObject.walk()):
            if not att.is_attachment(): continue

            type = att.get_content_type()
            payload = att.get_payload(decode=True)
            # Ensure unique objectKeys for attachments
            filename = '{}-{}-{}'.format(snsData['receipt']['action']['objectKey'], i, att.get_filename())

            app.log.debug(filename)

            response = s3client.upload_file(payload, 'sinfiltrar-attachments', filename)
            parsedData['attachments'].append({
              'type': type,
              'filename': att.get_filename(),
              'url': response.url
            })

    app.log.debug('parsedData %s', parsedData)

#     r = requests.post(url, json = parsedData, headers = { 'Content-Type': 'application/json' })


