from chalicelib.db import db_query

class Issuer:

    data: None

    def __init__(self, data):
        self.data = data

    @classmethod
    def all(cls):
        query = "SELECT id, slug, name FROM issuers ORDER BY name desc LIMIT 50"
        issuers = db_query(query)
        return [cls(issuer) for issuer in issuers]

    @classmethod
    def from_email(cls, email):

        query = """
            SELECT issuers.* FROM issuers
            INNER JOIN issuer_emails ON issuers.id = issuer_emails.issuer_id
            WHERE issuer_emails.email = %s
        """

        data = db_query(query, (email, ))[0]

        return cls(data)

    def get_id(self):
        return self.data['id']

    def get_name(self):
        return self.data['name']


    def save(self):

          query = """
              INSERT INTO issuers
                  (id, slug, name, created_at)
              VALUES
                  (%s, %s, %s, %s)
              ON CONFLICT (id)
              DO UPDATE SET
                  slug=EXCLUDED.slug,
                  name=EXCLUDED.name,
                  created_at=EXCLUDED.created_at
              """

          result = db_query(query, (
              self.data['id'],
              self.data['slug'],
              self.data['name'],
              self.data['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
          ))
