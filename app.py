import os
from dotenv import load_dotenv

from flask import Flask, render_template, request, flash, redirect, session, g, request, url_for
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from functools import wraps

from forms import UserAddForm, LoginForm, MessageForm, CsrfProtectForm, UpdateUserForm, LikeButtonForm
from models import db, connect_db, User, Message, DEFAULT_IMAGE_URL, DEFAULT_HEADER_IMAGE_URL

load_dotenv()

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
# toolbar = DebugToolbarExtension(app)

connect_db(app)

##############################################################################
# User signup/login/logout



@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

@app.before_request
def add_csrfform_to_g():
    """If we're logged in, add curr user to Flask global."""

    g.csrf_form = CsrfProtectForm()


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")


def login_required(f):
    @wraps(f)
    def login_decorator(*args, **kwargs):
        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")
        return f(*args, **kwargs)
    return login_decorator



def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Log out user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    do_logout()

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login and redirect to homepage on success."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(
            form.username.data,
            form.password.data,
        )

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)

@app.post('/logout')
def logout():
    """Handle logout of user and redirect to homepage."""

    if g.csrf_form.validate_on_submit():
        do_logout()
        flash('Successfully logged out.', 'success')
        return redirect(url_for('login'))

    flash("Access unauthorized.", "danger")
    return redirect("/")


##############################################################################
# General user routes:

@app.get('/users')
@login_required
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')
    blocked_by_ids = [user.id for user in g.user.blockers]

    if not search:
        users = (User
                    .query
                    .filter(User.id.not_in(blocked_by_ids))
                    .all())
    else:
        users = (User
                    .query
                    .filter(and_(
                        User.username.like(f"%{search}%"),
                        User.id.not_in(blocked_by_ids)),)
                    .all()
                )

    return render_template('users/index.html', users=users)


@app.get('/users/<int:user_id>')
@login_required
def show_user(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    blocked_by_ids = [user.id for user in g.user.blockers]

    if user.id in blocked_by_ids:
        return (render_template('404.html'), 404)

    return render_template('users/show.html', user=user)


@app.get('/users/<int:user_id>/following')
@login_required
def show_following(user_id):
    """Show list of people this user is following."""

    user = User.query.get_or_404(user_id)

    blocked_by_ids = [user.id for user in g.user.blockers]

    if user.id in blocked_by_ids:
        return (render_template('404.html'), 404)

    return render_template('users/following.html', user=user)


@app.get('/users/<int:user_id>/followers')
@login_required
def show_followers(user_id):
    """Show list of followers of this user."""

    user = User.query.get_or_404(user_id)

    blocked_by_ids = [user.id for user in g.user.blockers]

    if user.id in blocked_by_ids:
        return (render_template('404.html'), 404)

    return render_template('users/followers.html', user=user)


@app.post('/users/follow/<int:follow_id>')
@login_required
def start_following(follow_id):
    """Add a follow for the currently-logged-in user.

    Redirect to following page for the current for the current user.
    """
    if not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.post('/users/stop-following/<int:follow_id>')
@login_required
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user.

    Redirect to following page for the current for the current user.
    """
    if not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(url_for('show_following', user_id=g.user.id))
    # return redirect(f"/users/{g.user.id}/following")


@app.post('/users/block/<int:block_id>')
@login_required
def start_block(block_id):
    """Add a blocked user for the currently-logged-in user.

    Redirect back to blocked user's page.
    """

    if not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    blocked_user = User.query.get_or_404(block_id)
    g.user.blocking.append(blocked_user)
    db.session.commit()

    if g.user in  blocked_user.following:
        blocked_user.following.remove(g.user)

    db.session.commit()

    return redirect(f"/users/{blocked_user.id}")


@app.post('/users/stop-blocking/<int:block_id>')
@login_required
def stop_blocking(block_id):
    """Have currently-logged-in-user stop blocking this user.

    Redirect back to unblocked user's page.
    """
    if not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    blocked_user = User.query.get_or_404(block_id)
    g.user.blocking.remove(blocked_user)
    db.session.commit()

    return redirect(f"/users/{blocked_user.id}")


@app.route('/users/profile', methods=["GET", "POST"])
@login_required
def profile():
    """Update profile for current user."""

    form = UpdateUserForm(obj=g.user)

    if form.validate_on_submit():
        if User.authenticate(g.user.username, form.password.data):
            try:
                g.user.username = form.username.data
                g.user.email = form.email.data
                g.user.image_url = form.image_url.data or DEFAULT_IMAGE_URL
                g.user.header_image_url = form.header_image_url.data or DEFAULT_HEADER_IMAGE_URL
                g.user.bio = form.bio.data
                g.user.location = form.location.data

                db.session.commit()

            except IntegrityError:
                db.session.rollback()
                flash("Username already taken", 'danger')
                return render_template("users/edit.html", form=form)


            return redirect(f'/users/{g.user.id}')

        else:
            flash("Invalid credentials.", 'danger')

    return render_template("users/edit.html", form=form)


@app.post('/users/delete')
@login_required
def delete_user():
    """Delete user.

    Redirect to signup page.
    """

    if not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    Message.query.filter(Message.user_id == g.user.id).delete()
    db.session.commit()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


@app.get('/users/<int:user_id>/likes')
@login_required
def show_user_likes(user_id):
    """Shows page of user likes"""

    user = User.query.get_or_404(user_id)

    blocked_by_ids = [user.id for user in g.user.blockers]

    if user.id in blocked_by_ids:
        return (render_template('404.html'), 404)

    return render_template('users/likes.html', user=user)


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
@login_required
def add_message():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/create.html', form=form)


@app.get('/messages/<int:message_id>')
@login_required
def show_message(message_id):
    """Show a message."""

    msg = Message.query.get_or_404(message_id)

    blocked_by_ids = [user.id for user in g.user.blockers]

    if msg.user_id in blocked_by_ids:
        return (render_template('404.html'), 404)

    return render_template('messages/show.html', message=msg)


@app.post('/messages/<int:message_id>/delete')
@login_required
def delete_message(message_id):
    """Delete a message.

    Check that this message was written by the current user.
    Redirect to user page on success.
    """

    msg = Message.query.get_or_404(message_id)

    if not g.csrf_form.validate_on_submit() or msg.user_id != g.user.id:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")

@app.post('/messages/<int:message_id>/like')
@login_required
def like_message(message_id):
    """Like or unlike a message depending if the user has already liked or not"""

    if not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    current_url = request.form.get("current_url", '/')

    msg = Message.query.get_or_404(message_id)

    if msg in g.user.likes:
        g.user.likes.remove(msg)

    else:
        g.user.likes.append(msg)

    db.session.commit()

    return redirect(f'{current_url}')


##############################################################################
# Homepage and error pages


@app.get('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of self & followed_users
    """

    if g.user:
        following_ids = [user.id for user in g.user.following] + [g.user.id]
        messages = (Message
                    .query
                    .filter(Message.user_id.in_(following_ids))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        return render_template('home.html', messages=messages)

    else:
        return render_template('home-anon.html')


@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response
