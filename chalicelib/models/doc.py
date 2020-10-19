import base64
import json
import mailparser
from slugify import slugify

from chalicelib.aws import s3, s3client, bucket_name, bucket_location, AWS_INPUT_BUCKET_NAME
from chalicelib.db import db_query
from chalicelib.models.issuer import Issuer

class Doc(dict):

    data = None

    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return json.dumps(self.data)

    @classmethod
    def get_by_issuer(cls, issuer):
        query = 'SELECT * FROM docs WHERE issuer_id = %s ORDER BY issued_at'
        issuer_id = issuer.get_id()
        results = db_query(query, (issuer_id, ))
        return [cls(row) for row in results]

    @classmethod
    def from_s3(cls, objectKey):

        file = s3.Object(AWS_INPUT_BUCKET_NAME, objectKey)
#         app.log.debug('Downloading from %s/%s', bucketName, objectKey)

        mailBody = file.get()['Body'].read().decode('utf-8')
#         app.log.debug('Got body from %s/%s', bucketName, objectKey)

        return cls.from_string(mailBody, objectKey)

    @classmethod
    def from_string(cls, raw_email, key):
        mail = mailparser.parse_from_string(raw_email)
        data = {
            'id': key,
            'title': mail.subject,
            'from_email': mail._from,
            'body_html': mail.body,
            'body_plain': mail.body,
            'media': [],
            'date': mail.date,
        }

        for i, att in enumerate(mail.attachments):

            # Ensure unique objectKeys for attachments
            filename = '{}-{}-{}'.format(key, i, att['filename'])

            response = s3client.put_object(
                    ACL='public-read',
                    Body=base64.b64decode(att['payload']),
                    Bucket=bucket_name,
                    ContentType=att['mail_content_type'],
                    Key=filename,
            )

            location = s3client.get_bucket_location(Bucket=bucket_name)['LocationConstraint']
            url = "%s/%s" % (bucket_location, filename)
            cid = att['content-id'].strip('<>')

            data['media'].append({
                'type': att['mail_content_type'],
                'filename': att['filename'],
                'url': url,
                'cid': cid,
            })

        # if we only got html
        if not 'body_plain' in data and 'body_html' in data:
            data['body_plain'] = data['body_html'] # TODO: strip html

        # if we only got plain text
        if not 'body_html' in data and 'body_plain' in data:
            data['body_html'] = data['body_plain']

        # update src of embedded images
        if 'body_html' in data:
            for att in data['media']:
                if att['cid']:
                    data['body_html'] = data['body_html'].replace('cid:{}'.format(att['cid']), att['url'])

        issuer = Issuer.from_email(data['from_email'][0][1])

        data['issuer_id'] = issuer.get_id() if isinstance(issuer, Issuer) else None
        data['issuer_name'] = issuer.get_name() if isinstance(issuer, Issuer) else None

        return cls(data)


    def save(self):

          query = """
              INSERT INTO docs
                  (id, issuer_id, issuer_name, from_email, slug, title, short_text, body_html, body_plain, media, meta, issued_at)
              VALUES
                  (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              ON CONFLICT (id)
              DO UPDATE SET
                  issuer_id=EXCLUDED.issuer_id,
                  issuer_name=EXCLUDED.issuer_name,
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

          result = db_query(query, (
              self.data['id'],
              self.data['issuer_id'],
              self.data['issuer_name'],
              self.data['from_email'],
              slugify(self.data['title']),
              self.data['title'],
              self.data['body_plain'][:255],
              self.data['body_html'],
              self.data['body_plain'],
              json.dumps([{k: v for k, v in m.items() if k in ['type', 'url', 'filename']} for m in self.data['media']]),
              json.dumps({}),
              self.data['date'].strftime('%Y-%m-%d %H:%M:%S'),
          ))
