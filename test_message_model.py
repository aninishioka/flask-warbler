"""User message tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Like

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

class UserMessageTestCase(TestCase):
    def setUp(self):
        """Add sample data"""

        Like.query.delete()

        Message.query.delete()

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
        """Clean up any fouled transaction."""

        db.session.rollback()


    def test_create_message_success(self):
        """Test message creation"""

        u1 = User.query.get(self.u1_id)
        msg = Message.query.get(self.msg1_id)

        self.assertIsInstance(msg, Message)
        self.assertEqual(len(u1.messages), 1)
        self.assertEqual(msg.text, "test_msg")


    def test_create_message_fail_bad_user(self):
        """Test message creation with bad user"""

        with self.assertRaises(IntegrityError):
            msg = Message(text="test_msg", user_id=self.u2_id + 1)
            db.session.add(msg)
            db.session.commit()


    def test_create_message_fail_null_text(self):
        """Test message creation with bad text"""

        with self.assertRaises(IntegrityError):
            msg = Message(text=None, user_id=self.u2_id)
            db.session.add(msg)
            db.session.commit()


    def test_message_like(self):
        """Test message like"""

        msg = Message.query.get(self.msg1_id)
        u2 = User.query.get(self.u2_id)

        msg.liked_by.append(u2)
        db.session.commit()

        self.assertEqual(len(msg.liked_by), 1)
        self.assertIn(u2, msg.liked_by)
        self.assertEqual(len(u2.likes), 1)


    def test_message_delete_like(self):
        """Test delete message like"""

        msg2 = Message(text="test_text_2", user_id=self.u2_id)
        db.session.add(msg2)
        db.session.commit()

        u1 = User.query.get(self.u1_id)

        msg2.liked_by.append(u1)
        db.session.commit()

        self.assertEqual(len(u1.likes), 1)
        self.assertEqual(len(msg2.liked_by), 1)

        msg2.liked_by.remove(u1)
        db.session.commit()

        self.assertEqual(len(u1.likes), 0)
        self.assertEqual(len(msg2.liked_by), 0)



    def test_delete_message(self):
        """Test delete message"""

        msg = Message.query.get(self.msg1_id)

        db.session.delete(msg)
        db.session.commit()

        u1 = User.query.get(self.u1_id)

        self.assertEqual(len(u1.messages), 0)


    def test_delete_user_message_cascade(self):
        """Test deletion cascade on message when delete user"""

        u1 = User.query.get(self.u1_id)
        db.session.delete(u1)

        with self.assertRaises(IntegrityError):
            Message.query.get(self.msg1_id)


    def test_delete_message_likes_cascade(self):
        """Test deletion cascade on likes when delete message"""

        msg = Message.query.get(self.msg1_id)
        u2 = User.query.get(self.u2_id)

        msg.liked_by.append(u2)
        db.session.commit()

        db.session.delete(msg)
        db.session.commit()

        self.assertEqual(len(u2.likes), 0)


