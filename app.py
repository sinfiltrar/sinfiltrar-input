import datetime
import json
import logging
import os
import psycopg2
import psycopg2.extras
import requests
from pprint import pprint
from chalice import Chalice
from chalice import NotFoundError
from chalice import CORSConfig
from chalicelib.db import db_conn, db_query
from chalicelib.aws import s3, boto3
from chalicelib.models.doc import Doc
from chalicelib.models.issuer import Issuer

app = Chalice(app_name='sinfiltrar-input')
app.log.setLevel(logging.INFO)
app.debug = True

cors_config = CORSConfig(
    allow_origin=os.environ["ALLOW_ORIGIN"],
    allow_headers=['X-Special-Header'],
    max_age=600,
    expose_headers=['X-Special-Header'],
    allow_credentials=True
)

@app.route('/latest', cors=cors_config)
def latest():
    query = "SELECT * FROM docs ORDER BY issued_at DESC LIMIT 20"
    result = db_query(query)

    response = [{
      "title": doc['title'],
      "slug": doc['slug'],
      "short_text": doc['short_text'],
      "content": doc['body_plain'],
      "date": doc['issued_at'].__str__(),
      "media": doc['media'],
    } for doc in result]

    return response

@app.route('/issuers', cors=cors_config)
def all_issuers():
    issuers = Issuer.all()
    return json.dumps([issuer.data for issuer in issuers])

@app.route('/releases/{slug}', cors=cors_config)
def release(slug):
    query = "SELECT * FROM docs WHERE slug = %s"

    try:
        doc = db_query(query, (slug,))[0]
    except IndexError:
        raise NotFoundError("Release not found.")

    response = {
      "title": doc['title'],
      "slug": doc['slug'],
      "short_text": doc['short_text'],
      "content": doc['body_plain'],
      "date": doc['issued_at'].__str__(),
      "media": doc['media'],
    }

    return response


@app.on_sns_message(topic='sinfiltrar-input')
def handle_sns_message(event):
    snsData = json.loads(event.message)
    doc = Doc.from_s3(snsData['receipt']['action']['objectKey'])
    doc.save()


# @app.route('/all', cors=cors_config)
# def process_existing_s3_endpoint():
#     process_existing_s3(None, None)


@app.lambda_function()
def process_existing_s3(event, context):
    sns = boto3.client('sns')
    bucket = s3.Bucket('sinfiltrar-input')

    app.log.debug('Connected to bucket')
    for object in bucket.objects.all():
        app.log.debug('Sending sns %s', object.key)
        # Publish a simple message to the specified SNS topic
        response = sns.publish(
            TopicArn='arn:aws:sns:us-west-2:153920312805:sinfiltrar-input',
            Message=json.dumps({ 'receipt': { 'action': { 'bucketName': object.bucket_name, 'objectKey': object.key } } }),
        )


def process_email_from_bucket(bucketName, objectKey):

    file = s3.Object(bucketName, objectKey)
    app.log.debug('Downloading from %s/%s', bucketName, objectKey)

    mailBody = file.get()['Body'].read().decode('utf-8')
    app.log.debug('Got body from %s/%s', bucketName, objectKey)

    data = process_email_string(mailBody, objectKey)
    app.log.debug('data %s', data)

    doc = Doc.from_s3(objectKey)

    doc.save()




