"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follow, DEFAULT_HEADER_IMAGE_URL, DEFAULT_IMAGE_URL

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


class UserModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        u1 = User.query.get(self.u1_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)

    def test_is_following_none(self):
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.assertFalse(u2.is_following(u1))
        self.assertFalse(u1.is_following(u2))



    def test_is_following_one(self):
        new_follow = Follow(
            user_being_followed_id=self.u1_id,
            user_following_id=self.u2_id)

        db.session.add(new_follow)
        db.session.commit()

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.assertTrue(u2.is_following(u1))
        self.assertFalse(u1.is_following(u2))

    def test_is_following_both(self):
        first_follow = Follow(
            user_being_followed_id=self.u1_id,
            user_following_id=self.u2_id)

        second_follow = Follow(
            user_being_followed_id=self.u2_id,
            user_following_id=self.u1_id)

        db.session.add(first_follow)
        db.session.add(second_follow)
        db.session.commit()

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.assertTrue(u2.is_following(u1))
        self.assertTrue(u1.is_following(u2))

    def test_is_followed_by_none(self):
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.assertFalse(u2.is_followed_by(u1))
        self.assertFalse(u1.is_followed_by(u2))

    def test_is_followed_by_one(self):
        new_follow = Follow(
            user_being_followed_id=self.u1_id,
            user_following_id=self.u2_id)

        db.session.add(new_follow)
        db.session.commit()

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.assertTrue(u1.is_followed_by(u2))
        self.assertFalse(u2.is_followed_by(u1))

    def test_is_followed_by_both(self):
        first_follow = Follow(
            user_being_followed_id=self.u1_id,
            user_following_id=self.u2_id)

        second_follow = Follow(
            user_being_followed_id=self.u2_id,
            user_following_id=self.u1_id)

        db.session.add(first_follow)
        db.session.add(second_follow)
        db.session.commit()

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.assertTrue(u1.is_followed_by(u2))
        self.assertTrue(u2.is_followed_by(u1))

    def test_user_signup_success(self):
        u3 = User.signup("u3", "u3@email.com", "password", None)

        self.assertEqual(User.query.count(), 3)
        self.assertEqual(u3.image_url, DEFAULT_IMAGE_URL)
        self.assertEqual(u3.header_image_url, DEFAULT_HEADER_IMAGE_URL)
        self.assertIsInstance(u3, User)

    def test_user_signup_fail_username(self):
        with self.assertRaises(IntegrityError):
            User.signup("u2", "u3@email.com", "password", None)
            db.session.commit()

    def test_user_signup_fail_email(self):      #Why do we need to break up?
        with self.assertRaises(IntegrityError):
            User.signup("u3", "u2@email.com", "password", None)
            db.session.commit()

    def test_user_signup_fail_null(self):
        with self.assertRaises(ValueError):
            User.signup("u3", "u3@email.com", None)

    def test_user_authenticate_success(self):
        u2 = User.authenticate("u2", "password")

        self.assertIsInstance(u2, User)
        self.assertEqual(u2.username, 'u2')

    def test_user_authenticate_fail_username(self):
        u5 = User.authenticate("u5", "password")

        self.assertFalse(u5)

    def test_user_authenticate_fail_password(self):
        u2 = User.authenticate("u2", "passwordfail")

        self.assertFalse(u2)