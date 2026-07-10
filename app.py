import os
import git
from flask import Flask, render_template, url_for, redirect, request, session, jsonify
from datetime import datetime, date
from forms.noteMakerForm import NoteMakerForm
from werkzeug.utils import secure_filename
from functools import wraps

from models import Entry, get_all_by_user, add_entry, get_by_date, update_entry
from database import db

from spotify_api import SpotifyClient
from database import db

from gemini import SongGenerator

from dotenv import load_dotenv

from models import SpotifyToken, save_spotify_tokens, get_spotify_tokens, delete_spotify_tokens
app = Flask(__name__)

app.config['SECRET_KEY'] = 'overly=secure-token-4-testin@' #change this when pushing to server

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

load_dotenv()

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
    """
    Renders the initial landing page of the website

    Returns:
        HTML: Renders home.html
    """
    return render_template('home.html',subtitle='Home Page', text='This is the home page')


@app.route("/login/spotify")
def spotify_login():
    """
    Redirects user to log in with Spotify OAuth for app access

    Returns:
        Redirect: Sends the user to Spotify login page
    """
    spotify = SpotifyClient()
    login_url = spotify.build_user_login_url()
    return redirect(login_url)


# spotify sends user to /callback
@app.route("/callback")
def spotify_callback():
    """
    Receives a response from Spotify OAuth after user logs in
    Exchanges authorization code to access tokens and stores them in the database

    Query Parameters:
        code: The authorization code received from Spotify OAuth

    Returns:
        Redirect: Sends the user to the calendar page
    """
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
    """
    Logs the user out of the app and returns to the homepage

    Returns:
        Redirect: Sends user back to home
    """
    session.clear()
    return redirect(url_for("home"))
  
@app.route("/search-song")
def search_song():
    """
    Queries Spotify API for songs based on user input
    Requires user to be logged in

    Query Parameters:
        q (str): the query inputted by the user
    
    Returns:
        JSON: The list of songs returned by Spotify after searching
    """
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
    """
    Renders the about page of the app

    Returns:
        HTML: Renders about.html
    """
    return render_template('about.html', subtitle='About Page', text='This is the about page')


@app.route("/calendar")
@login_required
def calendar():
    """
    Renders the interactive calendar page with the user's recorded entries
    The entries are fetched from the database and injected to the calendar

    Returns:
        HTML: Renders calendar.html with user_notes data from table
    """
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
    """
    Renders the detailed note view of a specific date

    Query Parameters:
        date (str): The specified date in 'YYYY-MM-DD' format

    Returns:
        HTML: Renders note.html with the specified date if it exists
        Redirects: Sends the user back to the calendar page if the note doesn't exist
    """
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

    # gets song recommendations from Gemini
    testing_mode = os.getenv("SKIP_GEMINI", "false").lower() == "true"
    if testing_mode:
        recs = [
            {"name": "Africa", "artist": "Toto"},
            {"name": "Landslide", "artist": "Fleetwood Mac"},
            {"name": "Somebody to Love", "artist": "Queen"},
        ]
    else:
        s_generator = SongGenerator()
        recs = s_generator.get_songs(note_data['song'], note_data['notes'], note_data['location'])

    # uses Spotify API to search Spotify for the songs from Gemini
    # load in spotify tokens from user
    token_data = get_spotify_tokens(user_id)
    songs = []

    if token_data is None:
        songs = []
    else:
        # if token data exists we put in the saved spotify token data into the fresh spotify client so we can search tracks
        spotify = SpotifyClient()

        spotify.access_token = token_data["access_token"]
        spotify.refresh_token = token_data["refresh_token"]
        spotify.expires_at = token_data["expires_at"]

        # look up the saved song directly instead of parsing spotify_link
        saved_results = spotify.search_track(f"{entry.song_name} {entry.artist_name}")
        if saved_results:
            track_id = saved_results[0]['uri'].split(':')[-1]

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
            
        save_spotify_tokens(user_id, {
            "access_token": spotify.access_token,
            "refresh_token": spotify.refresh_token,
            "expires_at": spotify.expires_at
        })
    
    note_data = {
        "song": entry.song_name,
        "track_id": track_id,
        "photo": entry.photo_path, 
        "notes": entry.journal_text,
        "location": [entry.latitude, entry.longitude]
    }

    lat = entry.latitude
    lng = entry.longitude

    return render_template('note.html', subtitle='Note page', text='This is the note page', 
    note=note_data, date = chosen_date, songs=songs,
    latitude=lat, longitude=lng)


@app.route("/noteMaker", methods=["GET", "POST"])
@login_required
def noteMaker():
    """
    Renders the notemaker form to make a new note entry
    Also processes the form submission and interacts with database

    Query Parameters (GET):
        date (str, optional): if Get method, prefills the date for form submission

    Methods:
        GET: Displays an empty form with possibly pre-filled date
        POST: Receives form data, saves uploaded image, and records in the database

    Form Data (POST):
        latitude (str, optional): Latitude coordinate of note
        longitude (str, optional): Longitude coordinate of note
        song (str): Name of the chosen song
        location (str): The chosen location name
        notes (str): User inputted journal text
        date_created (str): Date formatted in 'YYYY-MM-DD'
        photo (File, optional): Optional image file uploaded by user
        spotify_artist (str): The chosen song's artist name
        spotify_uri (str): The uri to the song on Spotify
        spotify_image (str): The uri to the song's image on Spotify
    
    Returns:
        HTML: Renders noteMaker.html if GET method is called
        Redirect: Sends the user back to calendar on successful submission
    """
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
        existing_entry = get_by_date(user_id, entry_date)

        if existing_entry:
            update_entry(user_id, existing_entry.id,
                song_name=song,
                artist_name=spotify_artist,
                spotify_link=spotify_uri,
                song_image=spotify_image,
                location_name=location,
                photo_path=file_path if file_path else existing_entry.photo_path,
                journal_text=notes,
                latitude=lat,
                longitude=lng)
        else:
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
    """
    Renders the map page to see user's journal notes as location pins on the map

    Returns:
        HTML: Renders map.html
    """
    return render_template('map.html', subtitle='Map page', text='This is the map page')


@app.route("/entries/locations")
@login_required
def entry_locations():
    """
    Fetches location based entries to be rendered on the map for the user
    Ignores entries without a set latitude and longitude coordinate

    Returns:
        JSON: A list of entry objects
        Format:
        [
            {
                "id": int,
                "latitude": float,
                "longitude": float,
                "song_name": str,
                "date": str (YYYY-MM-DD)
            }
        ]
    """
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for('spotify_login'))
    entries = get_all_by_user(user_id)

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

@app.route("/update_server", methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo('/home/musicalmemories/Musical-Memories')
        origin = repo.remotes.origin
        origin.pull()
        return 'Updated PythonAnywhere successfully', 200
    else:
        return 'Wrong event type', 400
