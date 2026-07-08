import os
from flask import Flask, render_template, url_for, redirect, request, session, jsonify
from forms.noteMakerForm import NoteMakerForm
from spotify_api import SpotifyClient
from database import db
from models import SpotifyToken, save_spotify_tokens
app = Flask(__name__)

app.config['SECRET_KEY'] = 'overly=secure-token-4-testin@'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///models.db'

db.init_app(app)

@app.route("/")
def home():
    return render_template('home.html',subtitle='Home Page', text='This is the home page')

@app.route("/login/spotify")
def spotify_login():
    spotify = SpotifyClient()
    login_url = spotify.build_user_login_url()
    return redirect(login_url)

# spotify sends user to /callback
@app.route("/callback")
def spotify_callback():
    code = request.args.get("code")
    spotify = SpotifyClient()
    spotify.exchange_code_for_access_token(code)

    profile = spotify.get_user_profile()
    user_id = profile.get("account_id")

    # store user_id in flask session
    session["user_id"] = user_id

    # save user id and tokens into db
    save_spotify_tokens(user_id, {
        "access_token": spotify.access_token,
        "refresh_token": spotify.refresh_token,
        "expires_at": spotify.expires_at
    })

    return redirect("/calendar")



@app.route("/about")
def about():
    return render_template('about.html', subtitle='About Page', text='This is the about page')

@app.route("/calendar")
def calendar():
    return render_template('calendar.html', subtitle='Calendar Page', text='This is the calendar page')

@app.route("/note")
def note():
    return render_template('note.html', subtitle='Note page', text='This is the note page')

@app.route("/noteMaker", methods=["GET"])
def noteMaker():
    form = NoteMakerForm()
    if form.validate_on_submit():
        pass
    return render_template('noteMaker.html', subtitle='Note-Maker page', text='This is the note-maker page', form=form)
@app.route("/save-location", methods=["POST"])
def save_location():
    data = request.json
    locations.append(data)
    return jsonify({"status": "saved", "data": data})

@app.route("/locations")
def get_locations():
    return jsonify(locations)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
