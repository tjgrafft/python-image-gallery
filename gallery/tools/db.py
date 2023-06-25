import psycopg2
import json
from .secrets import get_secret_image_gallery


def read_secret_from_aws():
    json_string = get_secret_image_gallery()
    return json.loads(json_string)


def get_password(secret):
    return secret['password']


def get_host(secret):
    return secret['host']


def get_username(secret):
    return secret['username']


def get_dbname(secret):
    return secret['dbInstanceIdentifier']


class DbConnection:
    secret = None

    @classmethod
    def get_secret(cls):
        if cls.secret is not None:
            return cls.secret
        cls.secret = read_secret_from_aws()
        return cls.secret

    def __init__(self):
        self.connection = None

    def connect(self):
        secret = self.get_secret()
        self.connection = psycopg2.connect(host=get_host(secret), dbname=get_dbname(secret), user=get_username(secret),
                                           password=get_password(secret))

    def execute(self, query, args=None):
        cursor = self.connection.cursor()
        if not args:
            cursor.execute(query)
        else:
            cursor.execute(query, args)
        return cursor


def main():
    db = DbConnection()
    db.connect()
    res = db.execute('select * from users')
    for row in res:
        print(row)


if __name__ == '__main__':
    main()
