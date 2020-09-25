from chalice import Chalice
import requests
import json
import boto3
import email
import logging
import psycopg2
import os
import datetime

app = Chalice(app_name='sinfiltrar-input')
app.log.setLevel(logging.INFO)
# app.debug = True

# S3 init
bucket_name = 'sinfiltrar-attachments'
s3 = boto3.resource('s3', )
s3client = boto3.client('s3')

# RDS init
DB_ENDPOINT="sinfiltrar.c2yrjc7heqtk.us-west-2.rds.amazonaws.com"
DB_PORT="5432"
DB_USER="postgres"
DB_REGION="us-west-2"
DB_NAME="sinfiltrar"
DB_PASS="0WbkfeDvCP"

dbSession = boto3.Session()
rdsClient = boto3.client('rds')
token = rdsClient.generate_db_auth_token(DBHostname=DB_ENDPOINT, Port=DB_PORT, DBUsername=DB_USER, Region=DB_REGION)


@app.on_sns_message(topic='sinfiltrar-input')
def handle_sns_message(event):
    process_event(event)

def process_event(event):

    snsData = json.loads(event.message)
#     app.log.debug("Received message with subject: %s, message: %s", event.subject, event.message)
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
                cid = att['Content-ID'].strip('<>')

                parsedData['attachments'].append({
                    'type': content_type,
                    'filename': att.get_filename(),
                    'url': url,
                    'cid': cid,
                })

    # if we only got html
    if not 'body_plain' in parsedData and 'body' in parsedData:
        parsedData['body_plain'] = parsedData['body']  # TODO: strip html

    # if we only got plain text
    if not 'body' in parsedData and 'body_plain' in parsedData:
        parsedData['body'] = parsedData['body_plain']

    # body from bytes to string
    parsedData['body'] = '{}'.format(parsedData['body'])

    # update src of embedded images
    if 'body' in parsedData:
        for att in parsedData['attachments']:
            if att['cid']:
                app.log.debug('body %s', parsedData['body'])
                app.log.debug('cid %s', 'cid:{}'.format(att['cid']))
                app.log.debug('url %s', att['url'])
                parsedData['body'] = parsedData['body'].replace('cid:{}'.format(att['cid']), att['url'])

    app.log.debug('parsedData %s', parsedData)

    connection = db_conn()
    cursor = connection.cursor()
    query = "INSERT INTO docs (id, date, from_email, subject, body, body_plain, attachments) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    result = cursor.execute(query, (
        snsData['receipt']['action']['objectKey'],
        datetime.datetime.strptime(parsedData['date'], "%a, %d %b %Y %H:%M:%S %z").strftime('%Y-%m-%d %H:%M:%S'),
        parsedData['from'],
        parsedData['subject'],
        parsedData['body'],
        parsedData['body_plain'],
        json.dumps(parsedData['attachments'])
    ))
    connection.commit()
    cursor.close()
    connection.close()

def db_conn():
    try:
        conn = psycopg2.connect(host=DB_ENDPOINT, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS)
        return conn
    except Exception as e:
        app.log.warning("Database connection failed due to {}".format(e))
        exit()
