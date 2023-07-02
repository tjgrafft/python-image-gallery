from ..tools.db import db
from .user import User
from .user_dao import UserDAO

class PostgresUserDAO(UserDAO):
    def __init__(self):
        pass

    def get_users(self):
        result = []
        cursor = db.execute("select username,password,full_name from users")
        for t in cursor.fetchall():
            result.append(User(t[0], t[1], t[2]))
        return result
    
    def delete_user(self, username):
        db.execute("delete from users where username=%s", (username,))
        return     

    def get_user_by_username(self, username):
        cursor = db.execute("select username,password,full_name from users where username=%s", (username,))
        row = cursor.fetchone()
        if row is None:
            return None
        else:
            return User(row[0], row[1], row[2])
        