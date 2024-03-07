"""User message tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# app.config["TESTING"] = True

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

class UserViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

        msg1 = Message(text="test_msg", user_id=self.u1_id)
        db.session.add(msg1)
        db.session.commit()
        self.msg1_id = msg1.id

    def tearDown(self):
        db.session.rollback()


    def test_display_signup(self):
        with app.test_client() as client:
