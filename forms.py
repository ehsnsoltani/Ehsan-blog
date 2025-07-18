from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email, Length
from flask_ckeditor import CKEditorField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")



class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(message="Please Enter a name")])
    email = StringField("Email", validators=[DataRequired(), Email(message="Enter a valid email address")])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=4, max=24, message="Password length should be at least 4 and maximum 24")])
    submit = SubmitField("submit")


class LoginForm(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired(), Email(message="Enter a valid email address")])
    password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField("Let me in")


class CommentForm(FlaskForm):
    comment = CKEditorField("Comment", validators=[DataRequired(message="write some comment")])
    submit = SubmitField("SUBMIT COMMENT")

