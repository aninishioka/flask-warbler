"""Message View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# This is a bit of hack, but don't use Flask DebugToolbar

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)
        db.session.add_all([m1])
        db.session.commit()

        self.u1_id = u1.id
        self.m1_id = m1.id


    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()


class MessageAddViewTestCase(MessageBaseViewTestCase):
    def test_add_message(self):
        """Test adding a message"""
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            Message.query.filter_by(text="Hello").one()


    def test_add_message_unauthorized(self):
        """Test unauthorized user adding message"""

        with app.test_client() as client:

            response = client.post(
                "/messages/new",
                data={
                    "text": "Hello"
                },
                follow_redirects=True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)


    def test_add_empty_message(self):
        """Test failing message add by leaving text blank"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.post(
                "/messages/new",
                data={
                    "text": ""
                },
                follow_redirects=True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<button class="btn btn-outline-success">Add my message!</button>', html)


    def test_view_message_form(self):
        """Test showing the create message form"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.get('/messages/new')

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<button class="btn btn-outline-success">Add my message!</button>', html)



class MessageShowViewTestCase(MessageBaseViewTestCase):

    def test_view_message(self):
        """Test showing message page"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.get(f'/messages/{self.m1_id}')

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<!-- Test for the show message -->', html)
            self.assertIn('m1-text', html)


    def test_unauthorized_view_message(self):
        """Test unauthorized user not able to view message"""

        with app.test_client() as client:
            response = client.get(f'/messages/{self.m1_id}', follow_redirects=True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)


class MessageDeleteViewTestCase(MessageBaseViewTestCase):

    def test_delete_message(self):
        """Test delete message"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.post(
                f"/messages/{self.m1_id}/delete", follow_redirects=True)

            html = response.get_data(as_text=True)

            u1 = User.query.get(self.u1_id)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<!-- Test show user detail -->', html)
            self.assertNotIn("m1-text", html)
            self.assertEqual(len(u1.messages), 0)


    def test_unauthorized_delete_message(self):
        """Test unauthorized user not able to delete message"""

        with app.test_client() as client:
            response = client.post(f'/messages/{self.m1_id}/delete', follow_redirects=True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)


    def test_wrong_user_delete_message(self):
        """Test unauthorized user not able to delete message"""

        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.commit()

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = u2.id

            response = client.post(
                f'/messages/{self.m1_id}/delete',
                follow_redirects=True
                )

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.', html)
            self.assertIn('<!-- This is the signed in home page -->', html)



class MessageLikeViewTestCase(MessageBaseViewTestCase):
    def test_like_message_from_home(self):
        """Test Liking a message from home page"""

        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.commit()

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = u2.id

            u1 = User.query.get(self.u1_id)
            u2.following.append(u1)

            response = client.post(
                f'/messages/{self.m1_id}/like',
                data={
                    "current_url" : "/"
                },
                follow_redirects=True
                )

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('bi-star-fill', html)
            self.assertIn('<!-- This is the signed in home page -->', html)
            self.assertEqual(len(u2.likes), 1)


    def test_like_message_from_user_detail_page(self):
        """Test Liking a message from user detail page"""

        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.commit()

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = u2.id

            response = client.post(
                f'/messages/{self.m1_id}/like',
                data={
                    "current_url" : f"/users/{self.u1_id}"
                },
                follow_redirects=True
                )

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('bi-star-fill', html)
            self.assertIn('<!-- Test show user detail -->', html)
            self.assertEqual(len(u2.likes), 1)


    def test_unlike_message_from_home_page(self):
        """Test Liking a message from user detail page"""

        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.commit()

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = u2.id

            u1 = User.query.get(self.u1_id)
            u2.following.append(u1)

            m1 = Message.query.get(self.m1_id)
            u2.likes.append(m1)
            db.session.commit()

            response = client.post(
                f'/messages/{self.m1_id}/like',
                data={
                    "current_url" : "/"
                },
                follow_redirects=True
                )

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertNotIn('bi-star-fill', html)
            self.assertIn('bi-star', html)
            self.assertIn('<!-- This is the signed in home page -->', html)
            self.assertEqual(len(u2.likes), 0)


    def test_unauthorized_like(self):
        """Test unauthorized user liking message"""

        with app.test_client() as client:

            response = client.post(
                f'/messages/{self.m1_id}/like',
                data={
                    "current_url" : "/"
                },
                follow_redirects=True
                )

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)