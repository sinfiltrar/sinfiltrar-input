from chalicelib.db import db_query

class issuer_email:

    data = None

    def __init__(self, data):
        self.data = data

    @classmethod
    def get_or_create_by_email(cls, email):
        try:
            cls.from_email(email[1])
        except IndexError:
            cls.create_from_email(email)


    @classmethod
    def create_from_email(cls, email):
        self.data['email'] = email
        return cls(data)


    @classmethod
    def from_email(cls, email):
        data = db_query("SELECT * FROM issuer_emails WHERE email = %s", (email,))
        return cls(data)


    def save():

        query = """
            INSERT INTO issuer_email
                (email, issuer_id)
            VALUES
                (%s, %s)
            ON CONFLICT (id)
            DO UPDATE SET
            """

        result = db_query(query, (
            self.data['email'],
            self.data['issuer_id'],
        ))
