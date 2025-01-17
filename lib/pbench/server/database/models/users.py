import datetime
from flask_bcrypt import generate_password_hash
from email_validator import validate_email
from sqlalchemy import Column, Integer, String, DateTime, LargeBinary
from pbench.server.database.database import Database
from sqlalchemy.orm import relationship, validates


class User(Database.Base):
    """ User Model for storing user related details """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(255), unique=False, nullable=False)
    last_name = Column(String(255), unique=False, nullable=False)
    password = Column(LargeBinary(128), nullable=False)
    registered_on = Column(DateTime, nullable=False, default=datetime.datetime.now())
    email = Column(String(255), unique=True, nullable=False)
    auth_tokens = relationship("ActiveTokens", backref="users")

    def __str__(self):
        return f"User, id: {self.id}, username: {self.username}"

    def get_json(self):
        return {
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "registered_on": self.registered_on,
        }

    @staticmethod
    def get_protected():
        return ["registered_on", "id"]

    @staticmethod
    def query(id=None, username=None, email=None):
        # Currently we would only query with single argument. Argument need to be either username/id/email
        if username:
            user = Database.db_session.query(User).filter_by(username=username).first()
        elif id:
            user = Database.db_session.query(User).filter_by(id=id).first()
        elif email:
            user = Database.db_session.query(User).filter_by(email=email).first()
        else:
            user = None

        return user

    def add(self):
        """
        Add the current user object to the database
        """
        try:
            Database.db_session.add(self)
            Database.db_session.commit()
        except Exception:
            Database.db_session.rollback()
            raise

    @validates("password")
    def evaluate_password(self, key, value):
        return generate_password_hash(value)

    # validate the email field
    @validates("email")
    def evaluate_email(self, key, value):
        valid = validate_email(value)
        email = valid.email

        return email

    def update(self, **kwargs):
        """
        Update the current user object with given keyword arguments
        """
        try:
            for key, value in kwargs.items():
                if key == "auth_tokens":
                    # Insert the auth token
                    self.auth_tokens.append(value)
                    Database.db_session.add(value)
                else:
                    setattr(self, key, value)
            Database.db_session.commit()
        except Exception:
            Database.db_session.rollback()
            raise

    @staticmethod
    def delete(username):
        """
        Delete the user with a given username except admin
        :param username:
        :return:
        """
        try:
            user_query = Database.db_session.query(User).filter_by(username=username)
            user_query.delete()
            Database.db_session.commit()
            return True
        except Exception:
            Database.db_session.rollback()
            raise

    def is_admin(self):
        # TODO: Add notion of Admin user
        """this method would always return false for now until we add a notion of Admin user/group.
        Once we know the admin credentials this method can check against those credentials to determine
        whether the user is privileged to do more.

        This can be extended to groups as well for example a user belonging to certain group has only those
        privileges that are assigned to the group.
        """
        return False

    @staticmethod
    def is_admin_username(username):
        # TODO: Need to add an interface to fetch admins list instead of hard-coding the names, preferably via sql query
        admins = ["admin"]
        return username in admins

    # TODO: Add password recovery mechanism
