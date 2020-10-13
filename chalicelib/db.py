import psycopg2
import logging
from .aws import DB_ENDPOINT, DB_PORT, DB_NAME, DB_USER, token

logger = logging.getLogger('app')

# DB helpers

def db_conn():
    try:
        conn = psycopg2.connect(host=DB_ENDPOINT, port=DB_PORT, database=DB_NAME, user=DB_USER, password=token)
        return conn
    except Exception as e:
        logger.warning("Database connection failed due to {}".format(e))
        exit()


def db_query(query, values=None):
    connection = db_conn()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    fetch_all_as_dict = lambda cursor: [dict(row) for row in cursor]

    cursor.execute(query, values)

    try:
        result = fetch_all_as_dict(cursor)
    except psycopg2.ProgrammingError:
        result = None

    cursor.close()
    connection.close()
    return result

fetch_all_as_dict = lambda cursor: [dict(row) for row in cursor]
