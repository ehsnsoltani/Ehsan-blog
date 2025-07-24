from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
import hashlib
from http import HTTPStatus
from functools import wraps
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from telethon import TelegramClient

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)

Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


login_manager = LoginManager(app)



def get_gravatar_url(email, size=100):
    email = email.lower().strip().encode("utf-8")
    gravatar_hash = hashlib.md5(email).hexdigest()
    return f"https://www.gravatar.com/avatar/{gravatar_hash}?s={size}"

@app.context_processor
def inject_gravatar():
    return dict(get_gravatar_url=get_gravatar_url)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)



#only admin user
def only_admin(edit_post):
    @wraps(edit_post)
    def authenticate(*args, **kwargs):
        if current_user.get_id() == "1":
            return edit_post(*args, **kwargs)
        else:
            return abort(HTTPStatus.FORBIDDEN)


    return authenticate



##CONFIGURE TABLES

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    user_id = db.Column(db.Integer, ForeignKey("user.id"))
    user = relationship("User", back_populates="children")
    comments = relationship("Comment", back_populates="blog_post")


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    children = relationship("BlogPost", back_populates="user")
    comments = relationship("Comment", back_populates="user")





class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    user_id = db.Column(db.Integer, ForeignKey("user.id"))
    post_id = db.Column(db.Integer, ForeignKey("blog_posts.id"))

    blog_post = relationship("BlogPost", back_populates="comments")
    user = relationship("User", back_populates="comments")




@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        user = User.query.filter_by(email=register_form.data.get("email")).first()
        if not user:
            new_user = User(
                name=register_form.data.get("name"),
                email=register_form.data.get("email"),
                password=generate_password_hash(register_form.data.get("password"), "pbkdf2", salt_length=25)
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("get_all_posts"))

        else:
            flash("You've already signed up with that email, login instead!")
            return redirect(url_for("login"))

    return render_template("register.html", form=register_form)


@app.route('/login', methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.data.get("email")).first()
        if user:
            if check_password_hash(pwhash=user.password, password=login_form.data.get("password")):

                login_user(user)
                return redirect(url_for("get_all_posts"))

            else:
                flash("The password or email address is incorrect!")
                return redirect(url_for("login"))


        else:
            flash(message="You are not registered yet, register first!")
            return redirect(url_for("register"))

        return redirect(url_for("get_all_posts"))
    return render_template("login.html", form=login_form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    if requested_post:
        comment_form = CommentForm()

        if comment_form.validate_on_submit():
            if current_user.is_authenticated:
                new_comment = Comment(
                    text=comment_form.data.get("comment"),
                    user_id=current_user.id,
                    post_id=post_id

                )
                db.session.add(new_comment)
                db.session.commit()

                return redirect(url_for("show_post", post_id=post_id))
            else:
                flash("You need to login or register to comment")
                return redirect(url_for("login"))


        return render_template("post.html", post=requested_post, form=comment_form)
    else:
        return abort(HTTPStatus.NOT_FOUND)






@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=["GET", "POST"])
@login_required
@only_admin
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user.name,
            date=date.today().strftime("%B %d, %Y"),
            user_id=current_user.id
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)

@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required
@only_admin
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    if post:
        edit_form = CreatePostForm(
            title=post.title,
            subtitle=post.subtitle,
            img_url=post.img_url,
            author=post.author,
            body=post.body
        )
        if edit_form.validate_on_submit():
            post.title = edit_form.title.data
            post.subtitle = edit_form.subtitle.data
            post.img_url = edit_form.img_url.data
            post.author = edit_form.author.data
            post.body = edit_form.body.data
            db.session.commit()
            return redirect(url_for("show_post", post_id=post.id))
    else:
        return abort(HTTPStatus.NOT_FOUND)

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@only_admin
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))



@app.route("/bot")
def telegram():
    api_id = 25790013
    api_hash = "6a121918dd0424a943123b9d55071591"
    with TelegramClient("me", api_id, api_hash) as client:
        client.loop.run_until_complete(client.send_message('me', 'Hello, myself!'))



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
