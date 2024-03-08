"""User message tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY, g, DEFAULT_IMAGE_URL

app.config['WTF_CSRF_ENABLED'] = False

# app.config["TESTING"] = True

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

DEFAULT_HEADER_IMAGE_URL = 'https://images.unsplash.com/photo-1519751138087-5bf79df62d5b'

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


    def test_unauthorized_user_likes_route(self):                   #unauthenticated instead of unauthorized
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
            response = client.post(
            "/signup",
            data={
                "username": "u3",
                "password": "password",
                "email": "u3@email.com",
                "image_url": None
            },
            follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(g.user.id, self.u2_id + 1)                 #look at html (created username) not necessarily session (can change later)
            self.assertIn('<!-- This is the signed in home page -->', html)


    def test_user_signup_fail_bad_username(self):
        """Test user signup Route with bad username"""

        with app.test_client() as client:
            response = client.post(
            "/signup",
            data={
                "username": "u1",
                "password": "password",
                "email": "u3@email.com",
                "image_url": None
            },
            follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(g.user, None)
            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)
            self.assertIn("Username already taken", html)


    def test_user_signup_fail_short_password(self):
        """Test user signup Route with bad password"""

        with app.test_client() as client:
            response = client.post(
                "/signup",
            data={
                "username": "u1",
                "password": "12345",
                "email": "u3@email.com",
                "image_url": None
            },
            follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(g.user, None)
            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)


    def test_user_signup_fail_bad_email(self):
        """Test user signup Route with bad email"""

        with app.test_client() as client:
            response = client.post(
            "/signup",
            data={
                "username": "u3",
                "password": "password",
                "email": "u1@email.com",
                "image_url": None
            },
            follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(g.user, None)
            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)
            self.assertIn("Username already taken", html)   #StaffNote: Want to fix this eventually (email)


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


    def test_user_login_fail_bad_username(self):
        """Test user login route with bad username"""

        with app.test_client() as client:
            response = client.post("/login", data={
                "username": "u21",
                "password": "password"
            },
            follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(g.user, None)
            self.assertIn('<h2 class="join-message">Welcome back.</h2>', html)
            self.assertIn('Invalid credentials.', html)


    def test_user_login_fail_bad_password(self):
        """Test user login route with bad password"""

        with app.test_client() as client:
            response = client.post("/login", data={
                "username": "u2",
                "password": "password2"
            },
            follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(g.user, None)
            self.assertIn('<h2 class="join-message">Welcome back.</h2>', html)
            self.assertIn('Invalid credentials.', html)


    def test_unauthorized_start_following(self):
        with app.test_client() as client:
            response = client.post(f"/users/follow/{self.u1_id}", follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)


    def test_unauthorized_stop_following(self):
        with app.test_client() as client:
            response = client.post(f"/users/stop-following/{self.u1_id}", follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)


    def test_unauthorized_update_user(self):
        with app.test_client() as client:
            response = client.post(f"/users/profile", follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)


    def test_unauthorized_delete_user(self):
        with app.test_client() as client:
            response = client.post(f"/users/delete", follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)


class LoggedInUserGetViewTestCase(UserBaseViewTestCase):
    def test_home_page(self):
        """Test home page"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.get("/")

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<!-- This is the signed in home page -->', html)
            self.assertIn("test_msg", html)


    def test_list_users(self):
        """Test show list users"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.get("/users")

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<!-- Test users list -->', html)
            self.assertIn("u1", html)
            self.assertIn("u2", html)


    def test_search_list_users(self):
        """Test show list users"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.get(
                "/users",
                query_string = {
                    "q": "u1"
                }
            )

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<!-- Test users list -->', html)
            self.assertIn("u1", html)
            self.assertNotIn("u2", html)


    def test_specific_user(self):
        """Test show specific user"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.get(f"/users/{self.u1_id}")

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<!-- Test show user detail -->', html)
            self.assertIn("u1", html)


    def test_following_page(self):
        """Test show user following page"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            u1 = User.query.get(self.u1_id)
            u2 = User.query.get(self.u2_id)

            u1.following.append(u2)
            db.session.commit()

            response = client.get(f"/users/{self.u1_id}/following")

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<!-- Test following page -->', html)
            self.assertIn("u2", html)

    def test_followers_page(self):
        """Test show user followers page"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            u1 = User.query.get(self.u1_id)
            u2 = User.query.get(self.u2_id)

            u2.following.append(u1)
            db.session.commit()

            response = client.get(f"/users/{self.u1_id}/followers")

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<!-- Test followers page -->', html)
            self.assertIn("u2", html)


    def test_show_edit_user_form(self):
        """Test show edit user form."""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.get(f"/users/profile")

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Edit Your Profile.', html)
            self.assertIn('u1', html)


    def test_show_user_likes(self):
        """Test show edit user likes."""

        u2 = User.query.get(self.u2_id)
        u1_msg = Message.query.get(self.msg1_id)

        u1_msg.liked_by.append(u2)

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.get(f"/users/{self.u2_id}/likes")

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<!-- Test user likes page -->', html)
            self.assertIn('u1', html)
            self.assertIn('test_msg', html)




class LoggedInUserPostViewTestCase(UserBaseViewTestCase):
    def test_logout_success(self):
        """Test successful logout"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.post(f"/logout", follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<h2 class="join-message">Welcome back.</h2>', html)
            self.assertIn('Successfully logged out.', html)


    def test_start_following(self):
        """Test start following user"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.post(f"/users/follow/{self.u2_id}", follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<!-- Test following page -->', html)
            self.assertIn("u2", html)


    def test_start_following_nonexistent_user(self):
        """Test start following user"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.post(f"/users/follow/{self.u2_id + 1}", follow_redirects = True)      #primary key will never be 0 (better than self.u2_id + 1)

            self.assertEqual(response.status_code, 404)


    def test_stop_following(self):
        """Test start following user"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        u1.following.append(u2)
        db.session.commit()

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.post(f"/users/stop-following/{self.u2_id}", follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<!-- Test following page -->', html)
            self.assertNotIn("u2", html)


    def test_edit_user_profile(self):
        """Test submit edit user profile form"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.post(
                f"/users/profile",
                data={
                    "username": "u3",
                    "email": "u3@email.com",
                    "image_url": "",
                    "header_image_url": "",
                    "bio": "test_bio",
                    "location": "test_location",
                    "password": "password"
                },
                follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<!-- Test show user detail -->', html)
            self.assertIn("u3", html)
            self.assertIn("test_bio", html)
            self.assertIn("test_location", html)
            self.assertIn(DEFAULT_IMAGE_URL, html)
            self.assertIn(DEFAULT_HEADER_IMAGE_URL, html)


    def test_edit_user_profile_fail_bad_username(self):
        """Test submit edit user profile form with bad username"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.post(
                f"/users/profile",
                data={
                    "username": "u2",
                    "email": "u3@email.com",
                    "image_url": "",
                    "header_image_url": "",
                    "bio": "test_bio",
                    "location": "test_location",
                    "password": "password"
                },
                follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Edit Your Profile.', html)
            self.assertIn("Username already taken", html)


    def test_edit_user_profile_fail_bad_email(self):
        """Test submit edit user profile form with bad email"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.post(
                f"/users/profile",
                data={
                    "username": "u3",
                    "email": "u2@email.com",
                    "image_url": "",
                    "header_image_url": "",
                    "bio": "test_bio",
                    "location": "test_location",
                    "password": "password"
                },
                follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Edit Your Profile.', html)
            self.assertIn("Username already taken", html)


    def test_edit_user_profile_fail_bad_password(self):
        """Test submit edit user profile form with bad password"""

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.post(
                f"/users/profile",
                data={
                    "username": "u3",
                    "email": "u3@email.com",
                    "image_url": "",
                    "header_image_url": "",
                    "bio": "test_bio",
                    "location": "test_location",
                    "password": "aj;fkl"
                },
                follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Edit Your Profile.', html)
            self.assertIn("Invalid credentials", html)


    def test_delete_user(self):
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            response = client.post("/users/delete", follow_redirects = True)

            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)



