import os
from flask import Flask, render_template, url_for, redirect, request, session, jsonify
from datetime import datetime, date
from forms.noteMakerForm import NoteMakerForm
from werkzeug.utils import secure_filename
from functools import wraps

from models import Entry, get_all_by_user, add_entry
from database import db

from spotify_api import SpotifyClient
from database import db
from models import SpotifyToken, save_spotify_tokens, get_spotify_tokens, delete_spotify_tokens
app = Flask(__name__)

app.config['SECRET_KEY'] = 'overly=secure-token-4-testin@' #change this when pushing to server

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///models.db'
db.init_app(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            # If not logged in, boot them to the login screen
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login/dev-bypass")
def dev_bypass():
    # Force a mock user into the session
    session["user_id"] = "dev_test_user_123"
    
    # Send them straight into the protected app area
    return redirect(url_for("calendar"))



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

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))
  
@app.route("/search-song")
def search_song():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    # user must be logged in  
    user_id = session.get("user_id")

    if not user_id:
        return jsonify([])
    
    token_data = get_spotify_tokens(user_id)

    if token_data is None:
        return jsonify([])
    # resets tokens, but needed to call search_track
    spotify = SpotifyClient()

    # database tokens back into spotify client
    spotify.access_token = token_data["access_token"]
    spotify.refresh_token = token_data["refresh_token"]
    spotify.expires_at = token_data["expires_at"]

    songs = spotify.search_track(query)

    # access token might have been refreshed so we need to save new/current tokens in db
    save_spotify_tokens(user_id, {
        "access_token": spotify.access_token,
        "refresh_token": spotify.refresh_token,
        "expires_at": spotify.expires_at
    })

    return jsonify(songs)

# Protected App Routes

@app.route("/about")
@login_required
def about():
    return render_template('about.html', subtitle='About Page', text='This is the about page')

@app.route("/calendar")
@login_required
def calendar():
    user_id = session.get("user_id")
    notes_data = {}
    if user_id:
        entries = get_all_by_user(user_id)
        if entries:
            for entry in entries:
                entry_date = entry.date.strftime("%Y-%m-%d")
                notes_data[entry_date] = {
                    "text": entry.song_name,
                    "artist": entry.artist_name,
                    "spotify_link": entry.spotify_link,
                    "song_image": entry.song_image,
                    "notes": entry.journal_text,
                    "location": entry.location_name
                }
    return render_template('calendar.html', subtitle='Calendar Page', text='This is the calendar page', user_notes=notes_data)

@app.route("/note")
@login_required
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
@login_required
def noteMaker():
    form = NoteMakerForm()

    if request.method == "GET":
        url_date = request.args.get('date')
        if url_date:
            form.date_created.data = url_date
        else:
            form.date_created.data = datetime.today().strftime('%Y-%m-%d')

    if form.validate_on_submit():
        # Get user ID here
        user_id = session.get("user_id")

        if not user_id:
            return redirect(url_for("spotify_login"))

        lat = float(form.latitude.data) if form.latitude.data else None
        lng = float(form.longitude.data) if form.longitude.data else None

        
        song = form.song.data or ""
        spotify_uri = form.spotify_uri.data or ""
        spotify_image = form.spotify_image.data or ""
        spotify_artist = form.spotify_artist.data or ""
        location = form.location.data or ""
        notes = form.notes.data or None
        chosen_date = form.date_created.data
        

        photo_file = form.photo.data
        filename = None
        # if user does not submit a photo
        file_path = None

        if photo_file and photo_file.filename != '':    
            filename = secure_filename(photo_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo_file.save(file_path)

        date_array = form.date_created.data.split('-')
        entry_date = date(int(date_array[0]), int(date_array[1]), int(date_array[2]))

        # testing
        print("song:", song, type(song))
        print("spotify_artist:", spotify_artist, type(spotify_artist))
        print("spotify_uri:", spotify_uri, type(spotify_uri))
        print("spotify_image:", spotify_image, type(spotify_image))

        add_entry(user=user_id,
            date=entry_date,
            song=song,
            artist=spotify_artist,
            link=spotify_uri,
            song_image=spotify_image,
            location=location,
            photo=file_path,
            text=notes,
            latitude=lat,
            longitude=lng)
        
    
        return redirect(url_for('calendar'))
        
    return render_template('noteMaker.html', subtitle='Note-Maker page', text='This is the note-maker page', form=form)

@app.route("/map")
@login_required
def map():
    return render_template('map.html', subtitle='Map page', text='This is the map page')

@app.route("/entries/locations")
@login_required
def entry_locations():
    user_id = "user1" #maybe change to session["user_id"]
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
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)

@app.route("/update_server", methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo('/home/musicalmemories/Musical-Memories')
        origin = repo.remotes.origin
        origin.pull()
        return 'Updated PythonAnywhere successfully', 200
    else:
        return 'Wrong event type', 400
