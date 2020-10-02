import boto3
import datetime
import email
import json
import logging
import os
import psycopg2
import psycopg2.extras
import requests

from chalice import Chalice
from chalice import NotFoundError
from chalice import CORSConfig

from slugify import slugify

app = Chalice(app_name='sinfiltrar-input')
app.log.setLevel(logging.INFO)
app.debug = True

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

cors_config = CORSConfig(
    allow_origin='https://sinfiltr.ar http://sinfiltr.ar http://localhost:3000',
    allow_headers=['X-Special-Header'],
    max_age=600,
    expose_headers=['X-Special-Header'],
    allow_credentials=True
)

@app.route('/latest', cors=cors_config)
def latest():
    connection = db_conn()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    fetch_all_as_dict = lambda cursor: [dict(row) for row in cursor]
    query = "SELECT * FROM docs ORDER BY issued_at DESC LIMIT 20"
    cursor.execute(query)
    result = fetch_all_as_dict(cursor)
    cursor.close()
    connection.close()

    response = [{
      "title": doc['title'],
      "slug": doc['slug'],
      "short_text": doc['short_text'],
      "content": doc['body_plain'],
      "date": doc['issued_at'].__str__(),
      "media": doc['media'],
    } for doc in result]

    return response

@app.route('/releases/{slug}', cors=cors_config)
def release(slug):
    connection = db_conn()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = "SELECT * FROM docs WHERE slug = %s"
    cursor.execute(query, (slug,))

    try:
        doc = fetch_all_as_dict(cursor)[0]
    except IndexError:
        raise NotFoundError("Release not found.")

    cursor.close()
    connection.close()

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

    app.log.debug("Received message with subject: %s, message: %s", event.subject, event.message)
    app.log.debug('SNS DATA %s', snsData['mail']['commonHeaders'])
    snsData = json.loads(event.message)
    process_email_from_bucket(
      snsData['receipt']['action']['bucketName'],
      snsData['receipt']['action']['objectKey']
    )

@app.lambda_function()
def process_existing_s3():

    bucket = s3.Bucket('sinfiltrar-input')

    for object in bucket.objects.all():
      process_email_from_bucket(
        object.bucket_name,
        object.key
      )

def process_email_from_bucket(bucketName, objectKey):

    object = s3.Object(bucketName, objectKey)
    app.log.debug('Downloading from %s/%s', bucketName, objectKey)

    mailBody = object.get()['Body'].read().decode('utf-8')
    app.log.debug('Got body from %s/%s', bucketName, objectKey)

    emailObject = email.message_from_string(mailBody)
    data['subject'] = emailObject['Subject']
    data['from'] = emailObject['From']
    data['date'] = emailObject['Date']
    data['attachments'] = []

    if emailObject.is_multipart():
        for i, att in enumerate(emailObject.walk()):

            content_type = att.get_content_type()
            payload = att.get_payload(decode=True)

            if content_type == 'text/plain' and 'body_plain' not in data:
                data['body_plain'] = payload.decode('utf-8')
            elif content_type == 'text/html' and 'body' not in data:
                data['body'] = payload.decode('utf-8')
            elif payload != None:
                # Ensure unique objectKeys for attachments
                filename = '{}-{}-{}'.format(objectKey, i, att.get_filename())

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

                data['attachments'].append({
                    'type': content_type,
                    'filename': att.get_filename(),
                    'url': url,
                    'cid': cid,
                })
    else:
        data['body'] = emailObject.get_payload()
        data['body_plain'] = emailObject.get_payload()

    # if we only got html
    if not 'body_plain' in data and 'body' in data:
        data['body_plain'] = data['body'] # TODO: strip html

    # if we only got plain text
    if not 'body' in data and 'body_plain' in data:
        data['body'] = data['body_plain']

    # update src of embedded images
    if 'body' in data:
        for att in data['attachments']:
            if att['cid']:
                data['body'] = data['body'].replace('cid:{}'.format(att['cid']), att['url'])

    app.log.debug('data %s', data)

    connection = db_conn()
    cursor = connection.cursor()
    query = """
        INSERT INTO docs
            (id, from_email, slug, title, short_text, body_html, body_plain, media, meta, issued_at)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id)
        DO UPDATE SET
            from_email=EXCLUDED.from_email,
            slug=EXCLUDED.slug,
            title=EXCLUDED.title,
            short_text=EXCLUDED.short_text,
            body_html=EXCLUDED.body_html,
            body_plain=EXCLUDED.body_plain,
            media=EXCLUDED.media,
            meta=EXCLUDED.meta,
            issued_at=EXCLUDED.issued_at
        """
    result = cursor.execute(query, (
        objectKey,
        data['from'],
        slugify(data['subject']),
        data['subject'],
        data['body_plain'][:255],
        data['body'],
        data['body_plain'],
        json.dumps([{k: v for k, v in m.items() if k in ['type', 'url', 'filename']} for m in data['attachments']]),
        json.dumps({}),
        datetime.datetime.strptime(data['date'], "%a, %d %b %Y %H:%M:%S %z").strftime('%Y-%m-%d %H:%M:%S'),

    ))
    connection.commit()
    cursor.close()
    connection.close()


# DB helpers

def db_conn():
    try:
        conn = psycopg2.connect(host=DB_ENDPOINT, port=DB_PORT, database=DB_NAME, user=DB_USER, password=token)
        return conn
    except Exception as e:
        app.log.warning("Database connection failed due to {}".format(e))
        exit()

fetch_all_as_dict = lambda cursor: [dict(row) for row in cursor]
