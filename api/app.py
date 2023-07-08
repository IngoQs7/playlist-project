import os
from flask import Flask
from dotenv import load_dotenv
from pymongo import MongoClient

import functools
import uuid
import re
import datetime
from dataclasses import asdict

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    session,
    url_for,
    request,
)
from api.forms import LoginForm, RegisterForm, SongForm, ExtendedSongForm
from api.models import User, Song
from passlib.hash import pbkdf2_sha256

load_dotenv()

app = Flask(__name__)
app.config["MONGODB_URI"] = os.environ.get("MONGODB_URI")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.db = MongoClient(app.config["MONGODB_URI"]).get_default_database()


def login_required(route):
    @functools.wraps(route)
    def route_wrapper(*args, **kwargs):
        if session.get("email") is None:
            return redirect(url_for("login"))

        return route(*args, **kwargs)

    return route_wrapper


def datetime_formatting(song):

    time_ago = datetime.datetime.today() - song.date_added
    time_ago = time_ago.__str__()

    if time_ago.find("days") != -1 or time_ago.find("day") != -1:
        time_ago = time_ago[:(time_ago.find(","))]
        time_ago += ' ago'

    elif re.match("0:..:..", time_ago):
        time_ago = int(time_ago.split(':')[1])
        if time_ago >= 30 and time_ago <= 40:
            time_ago = "Half hour ago"
        elif time_ago >= 40:
            time_ago = "Almost an hour ago"
        else:
            time_ago = "Few minutes ago"

    else:
        time_ago = int(time_ago.split(':')[0])
        if time_ago == 1:
            time_ago = str(time_ago) + ' hour ago'
        else:
            time_ago = str(time_ago) + ' hours ago'

    return time_ago

    
@app.route("/")
@login_required
def index():
    user_data = current_app.db.user.find_one({"email": session["email"]})
    if not user_data:
        return redirect(url_for(".logout"))

    user = User(**user_data)
    song_data = current_app.db.song.find({"_id": {"$in": user.songs}})
    songs = [Song(**song) for song in song_data]

    return render_template(
        "index.html",
        title="Songs Playlist",
        songs_data=songs,
        datetime_formatting=datetime_formatting
    )


@app.route("/register", methods=["POST", "GET"])
def register():
    if session.get("email"):
        return redirect(url_for("index"))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            _id=uuid.uuid4().hex, 
            email=form.email.data, 
            password=pbkdf2_sha256.hash(form.password.data), 
        )                                                     

        current_app.db.user.insert_one(asdict(user))

        flash("User registered successfully", "success")
        return redirect(url_for("login"))

    return render_template(
        "register.html", title="Songs Playlist - Register", form=form
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("email"):
        return redirect(url_for("index"))

    form = LoginForm()
    if request.args.get('d') == 'demo':
        user_data = current_app.db.user.find_one({"email": "test@example.com"})
        user = User(**user_data)
        session["user_id"] = user._id
        session["email"] = user.email

        return redirect(url_for("index"))

    if form.validate_on_submit():
        
        user_data = current_app.db.user.find_one({"email": form.email.data})

        if not user_data:
            flash("Login credentials not correct", category="danger")
            return redirect(url_for("login"))

        user = User(**user_data)
        if user and pbkdf2_sha256.verify(form.password.data, user.password):
            session["user_id"] = user._id
            session["email"] = user.email

            return redirect(url_for("index"))

        flash("Login credentials not correct", category="danger")
        
    return render_template("login.html", title="Songs Playlist - Login", form=form)


@app.route("/logout")
def logout():
    del session["email"]
    del session["user_id"]

    return redirect(url_for("login"))


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_song():
    form = SongForm()
    
    if form.validate_on_submit():
        song = Song(
            _id=uuid.uuid4().hex,
            title=form.title.data,
            band=form.band.data,
            album=form.album.data,
            date_added=datetime.datetime.today()
        )

        current_app.db.song.insert_one(asdict(song))
        current_app.db.user.update_one(
            {"_id": session["user_id"]}, {"$push": {"songs": song._id}}
        )

        return redirect(url_for(".song", _id=song._id))
    return render_template(
        "new_song.html", title="Songs Playlist - Add Song", form=form
    )



@app.get("/song/<string:_id>")
def song(_id: str):
    song = Song(**current_app.db.song.find_one({"_id": _id}))
    return render_template("song_details.html", song=song)


@app.route("/edit/<string:_id>", methods=["GET", "POST"])
@login_required
def edit_song(_id: str):
    song = Song(**current_app.db.song.find_one({"_id": _id}))
    form = ExtendedSongForm(obj=song) 

    if form.validate_on_submit():
        song.title = form.title.data
        song.band = form.band.data
        song.album = form.album.data
        song.year = form.year.data
        song.tags = form.tags.data
        song.description = form.description.data
        song.video_link = form.video_link.data

        current_app.db.song.update_one({"_id": song._id}, {"$set": asdict(song)})
        return redirect(url_for(".song", _id=song._id))
    return render_template("song_form.html", song=song, form=form)


@app.get("/song/<string:_id>/play")
@login_required
def play_today(_id):
    
    current_app.db.song.update_one(
        {"_id": _id}, {"$set": {"last_played": datetime.datetime.today()}}
    )

    return redirect(url_for(".song", _id=_id))


@app.get("/song/<string:_id>/rate")
@login_required
def rate_song(_id):
    
    rating = int(request.args.get("rating"))
    current_app.db.song.update_one({"_id": _id}, {"$set": {"rating": rating}})

    return redirect(url_for(".song", _id=_id))


@app.get("/toggle-theme")
def toggle_theme():
    current_theme = session.get("theme")

    if current_theme == "dark":
        session["theme"] = "light"
    else:
        session["theme"] = "dark"

    return redirect(request.args.get("current_page"))

if __name__ == "__main__":
    app.run(debug=True)