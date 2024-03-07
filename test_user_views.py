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

from app import app, CURR_USER_KEY, g

app.config['WTF_CSRF_ENABLED'] = False

# app.config["TESTING"] = True

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

class UserBaseViewTestCase(TestCase):
    def setUp(self):
        """Add sample data."""

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



class AnonUserGetViewTestCase(UserBaseViewTestCase):
    def test_display_signup(self):
        """Test showing signup page"""

        with app.test_client() as client:
            response = client.get('/signup')

            html = response.get_data(as_text=True)

            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)
            self.assertEqual(response.status_code, 200)


    def test_display_login(self):
        """Test showing login page"""

        with app.test_client() as client:
            response = client.get('/login')

            html = response.get_data(as_text=True)

            self.assertIn('<h2 class="join-message">Welcome back.</h2>', html)
            self.assertEqual(response.status_code, 200)


    def test_display_home_anon(self):
        """Test showing logged out home page"""

        with app.test_client() as client:
            response = client.get('/')

            html = response.get_data(as_text=True)

            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertEqual(response.status_code, 200)


    def test_unauthorized_users_route(self):
        """Test unauthorized user can't access users route"""

        with app.test_client() as client:
            response = client.get('/users', follow_redirects=True)

            html = response.get_data(as_text=True)

            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn("Access unauthorized", html)
            self.assertEqual(response.status_code, 200)


    def test_unauthorized_specific_user_route(self):
        """Test unauthorized user can't access users route"""

        with app.test_client() as client:
            response = client.get(f'/users/{self.u1_id}', follow_redirects=True)

            html = response.get_data(as_text=True)

            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn("Access unauthorized", html)
            self.assertEqual(response.status_code, 200)


    def test_unauthorized_user_following_route(self):
        """Test unauthorized user can't access user following route"""

        with app.test_client() as client:
            response = client.get(f'/users/{self.u1_id}/following', follow_redirects=True)

            html = response.get_data(as_text=True)

            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn("Access unauthorized", html)
            self.assertEqual(response.status_code, 200)


    def test_unauthorized_user_followers_route(self):
        """Test unauthorized user can't access user followers route"""

        with app.test_client() as client:
            response = client.get(f'/users/{self.u1_id}/followers', follow_redirects=True)

            html = response.get_data(as_text=True)

            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn("Access unauthorized", html)
            self.assertEqual(response.status_code, 200)


    def test_unauthorized_user_profile_route(self):
        """Test unauthorized user can't access user profile route"""

        with app.test_client() as client:
            response = client.get(f'/users/profile', follow_redirects=True)

            html = response.get_data(as_text=True)

            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn("Access unauthorized", html)
            self.assertEqual(response.status_code, 200)


    def test_unauthorized_user_likes_route(self):
        """Test unauthorized user can't access user likes route"""

        with app.test_client() as client:
            response = client.get(f'/users/{self.u1_id}/likes', follow_redirects=True)

            html = response.get_data(as_text=True)

            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn("Access unauthorized", html)
            self.assertEqual(response.status_code, 200)



class AnonUserPostViewTestCase(UserBaseViewTestCase):
    def test_user_signup(self):
        """Test user signup Route"""

        with app.test_client() as client:
            response = client.post("/signup", data={
                "username": "u3",
                "password": "password",
                "email": "u3@email.com",
                "image_url": None
            },
            follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(g.user.id, self.u2_id + 1)
            self.assertIn('<!-- This is the signed in home page -->', html)

    def test_user_login(self):
        """Test user login route"""

        with app.test_client() as client:
            response = client.post("/login", data={
                "username": "u2",
                "password": "password"
            },
            follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(g.user.id, self.u2_id)
            self.assertIn('<!-- This is the signed in home page -->', html)