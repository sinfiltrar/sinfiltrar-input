from chalice import Chalice
import requests
import json
import boto3
import email

app = Chalice(app_name='sinfiltrar-input')
app.debug = True

bucket_name = 'sinfiltrar-attachments'
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

    if emailObject.is_multipart():
        for i, att in enumerate(emailObject.walk()):

            content_type = att.get_content_type()
            payload = att.get_payload(decode=True)

            if content_type == 'text/plain' and 'body_plain' not in parsedData:
                parsedData['body_plain'] = payload
            elif content_type == 'text/html' and 'body' not in parsedData:
                parsedData['body'] = payload
            elif payload != None:
                # Ensure unique objectKeys for attachments
                filename = '{}-{}-{}'.format(snsData['receipt']['action']['objectKey'], i, att.get_filename())

                response = s3client.put_object(
                        ACL='public-read',
                        Body=payload,
                        Bucket=bucket_name,
                        ContentType=content_type,
                        Key=filename,
                        )

                location = s3client.get_bucket_location(Bucket=bucket_name)['LocationConstraint']
                url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket_name, filename)

                parsedData['attachments'].append({
                  'type': content_type,
                  'filename': att.get_filename(),
                  'url': url
                })

    # TODO: change img src for related MIME parts

    if not 'body_plain' in parsedData and 'body' in parsedData:
        parsedData['body_plain'] = parsedData['body']  # TODO: strip html

    app.log.debug('parsedData %s', parsedData)
