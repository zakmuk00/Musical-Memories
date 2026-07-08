import os
from flask import Flask, render_template, url_for, request, redirect, jsonify
from datetime import datetime
from forms.noteMakerForm import NoteMakerForm
from werkzeug.utils import secure_filename

from entry import Entry, get_all_by_user, add_entry
from database import db

app = Flask(__name__)

app.config['SECRET_KEY'] = 'overly=secure-token-4-testin@' #change this when pushing to server

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
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
    chosen_date = request.args.get('date')
    if not chosen_date:
        return redirect(url_for('calendar'))

    # mock data take out
    note_data = {
        "song": "Bohemian Rhapsody",
        "photo": None, 
        "notes": "Had this song stuck in my head while driving through the mountains today.",
        "location": "Seattle, WA"
    }
    
    return render_template('note.html', subtitle='Note page', text='This is the note page', note=note_data, date = chosen_date)

@app.route("/noteMaker", methods=["GET", "POST"])
def noteMaker():
    form = NoteMakerForm()

    if request.method == "GET":
        url_date = request.args.get('date')
        if url_date:
            form.date_created.data = url_date
        else:
            form.date_created.data = datetime.today().strftime('%Y-%m-%d')

    if form.validate_on_submit():
        lat = float(form.latitude.data) if form.latitude.data else None
        lng = float(form.longitude.data) if form.longitude.data else None

        song = form.song.data
        location = form.location.data
        notes = form.notes.data
        chosen_date = form.date_created.data
        # Get user ID here and save both id and date to db

        photo_file = form.photo.data
        filename = None

        if photo_file and photo_file.filename != '':    
            filename = secure_filename(photo_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo_file.save(file_path)

        '''
        add_entry(user='dummy user',
            date='Date Here',
            song=form.song,
            link='Spotify Song Link Here',
            song_image='Spotify Album Image Here',
            location=form.location,
            photo=path
            text=form.notes,
            latitude=lat,
            longitude=lng)
        '''

        return redirect(url_for('calendar'))
        
    return render_template('noteMaker.html', subtitle='Note-Maker page', text='This is the note-maker page', form=form)

@app.route("/map")
def map():
    return render_template('map.html', subtitle='Map page', text='This is the map page')

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
