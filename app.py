import os
from flask import Flask, render_template, url_for, jsonify
from forms.noteMakerForm import NoteMakerForm
from entry import Entry, get_all_by_user
from database import db

app = Flask(__name__)

app.config['SECRET_KEY'] = 'overly=secure-token-4-testin@'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///entries.db'
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template('home.html',subtitle='Home Page', text='This is the home page')

@app.route("/login/spotify")
def spotify_login():
    spotify_auth_url = ""
    return redirect(spotify_auth_url)

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

@app.route("/map")
def map():
    return render_template('map.html', subtitle='Map page', text='This is the map page')

@app.route("/save-location", methods=["POST"])
def save_location():
    data = request.json
    locations.append(data)
    return jsonify({"status": "saved", "data": data})

@app.route("/entries/locations")
def entry_locations():
    user_id = "user1"
    entries = get_all_by_user(user_id)

    data = [
        {
            "id": e.id,
            "latitude": e.latitude,
            "longitude": e.longitude,
            "song_name": e.song_name,
            "date": e.date.isoformat()
        }
        for e in entries if e.latitude is not None and e.longitude is not None
    ]
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
