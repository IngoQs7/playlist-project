from flask_wtf import FlaskForm
from flask import current_app
from wtforms import (
    IntegerField,
    PasswordField,
    StringField,
    SubmitField,
    TextAreaField,
    URLField,
)

from wtforms.validators import (
    InputRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    ValidationError
)



class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Login")

def email_unique(form, field):
    if current_app.db.user.find_one({"email": field.data}):
        raise ValidationError("This email already exists.")
            

class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email(), email_unique])
    password = PasswordField(
        "Password",
        validators=[
            InputRequired(),
            Length(
                min=4,
                max=20,
                message="Your password must be between 4 and 20 characters long.",
            ),
        ],
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            InputRequired(),
            EqualTo(
                "password",
                message="This password did not match the one in the password field.",
            ),
        ],
    )

    submit = SubmitField("Register")



class SongForm(FlaskForm):
    title = StringField("Title", validators=[InputRequired()])
    band = StringField("Band", validators=[InputRequired()])
    album = StringField("Album", validators=[Optional()])


    submit = SubmitField("Add Song")


class StringListField(TextAreaField):
    def _value(self):
        if self.data:
            return "\n".join(self.data)
        else:
            return ""

    def process_formdata(self, valuelist):
        # checks valuelist contains at least 1 element, and the first element isn't falsy (i.e. empty string)
        if valuelist and valuelist[0]:
            self.data = [line.strip() for line in valuelist[0].split("\n")]
        else:
            self.data = []

def embed_validator(form, field):
        if field.data.find("youtu.be") != -1:
            field.data = field.data.replace("youtu.be", "www.youtube.com")
        if field.data.find("watch?v=") != -1:
            field.data = field.data.replace("watch?v=", "embed/")
        if field.data.find("/embed/") == -1:
            field.data = field.data.replace(".com/", ".com/embed/")
        if field.data.find("&") != -1:
            field.data = field.data[:(field.data.find("&"))]




class ExtendedSongForm(SongForm):
    year = IntegerField(
        "Year",
        validators=[
            Optional(),
            NumberRange(min=1800, message="Please enter a year in the format YYYY."),
        ],
    )
    tags = StringListField("Tags (one per line)")
    description = TextAreaField("Description")
    video_link = URLField("Video link", validators=[InputRequired(), embed_validator])

    submit = SubmitField("Submit")
