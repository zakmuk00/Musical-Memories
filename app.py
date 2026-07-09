import os
from flask import Flask, render_template, url_for, redirect, request, session, jsonify
from datetime import datetime
from forms.noteMakerForm import NoteMakerForm
from werkzeug.utils import secure_filename

from models import Entry, get_all_by_user, add_entry, get_by_date
from database import db

from spotify_api import SpotifyClient
from database import db
from models import SpotifyToken, save_spotify_tokens

from gemini import SongGenerator

app = Flask(__name__)

app.config['SECRET_KEY'] = 'overly=secure-token-4-testin@' #change this when pushing to server

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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
    chosen_date = request.args.get('date')
    if not chosen_date:
        return redirect(url_for('calendar'))
    
    user_id = session.get("user_id", "test_user_1")
    if not user_id:
        return redirect(url_for('spotify_login'))

    date = datetime.strptime(chosen_date, '%Y-%m-%d').date()
    entry = get_by_date(user_id, date)

    if entry is None:
        return redirect(url_for('calendar'))

    note_data = {
        "song": entry.song_name,
        "photo": entry.photo_path, 
        "notes": entry.journal_text,
        "location": entry.location_name
    }

    # gets song recommendations from Gemini
    s_generator = SongGenerator()
    recs = s_generator.get_songs(note_data['song'], note_data['notes'], note_data['location'])

    # uses Spotify API to search Spotify for the songs from Gemini
    spotify = SpotifyClient()
    songs = []
    for rec in recs:
        results = spotify.search_track(f"{rec['name']} {rec['artist']}")
        if results:
            track_id = results[0]['uri'].split(':')[-1]
        else:
            track_id = None
        songs.append({
            "name": rec['name'],
            "artist": rec['artist'],
            "track_id": track_id
        })

    return render_template('note.html', subtitle='Note page', text='This is the note page', note=note_data, date = chosen_date, songs=songs)


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

        date_array = form.date_created.data.split('-')
        entry_date = date(int(date_array[0]), int(date_array[1]), int(date_array[2]))

        '''
        add_entry(user=session.user_id,
            date=entry_date,
            song=form.song,
            link='Spotify Song Link Here',
            song_image='Spotify Album Image Here',
            location=form.location,
            photo=file_path,
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
    
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for('spotify_login'))

    entries = get_all_by_user(user_id)
    if entries is None:
        return redirect(url_for('calendar'))
    
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
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
