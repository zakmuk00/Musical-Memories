import os
import git
from flask import Flask, render_template, url_for,redirect, request, session, jsonify, flash
from datetime import datetime, date
from forms.note_maker_form import NoteMakerForm
from werkzeug.utils import secure_filename
from functools import wraps

from models import (
    Entry, get_all_by_user, add_entry, get_by_date, update_entry, delete_by_id,
    delete_by_date, get_or_create_user, send_request, respond_to_request,
    get_user_by_username, is_friend_of, get_friends, get_pending_outbound,
    get_pending_inbound, cancel_request,
    Calendar, get_or_create_personal_calendar, get_user_calendars,
    is_calendar_member, join_calendar_by_code, create_calendar,
    get_calendar_by_id, get_all_by_calendar, delete_calendar
)
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


def get_active_calendar_id():
    """
    Returns the id of the calendar the current user is currently viewing.
    Falls back to (and repairs the session to point at) their personal
    calendar if nothing valid is set yet.
    """
    user_id = session.get("user_id")
    calendar_id = session.get("active_calendar_id")

    if calendar_id and is_calendar_member(user_id, calendar_id):
        return calendar_id

    personal = get_or_create_personal_calendar(user_id)
    session["active_calendar_id"] = personal.id
    return personal.id


@app.route("/login/dev-bypass")
def dev_bypass():
    fake_id = request.args.get("as", "dev_test_user_1")
    session["user_id"] = fake_id
    session["username"] = fake_id
    get_or_create_user(fake_id, fake_id)
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

    user = get_or_create_user(user_id, profile.get("display_name"))
    # store useranme in flask session
    session["username"] = user.username

    # default the session to the user's personal calendar
    personal = get_or_create_personal_calendar(user_id)
    session["active_calendar_id"] = personal.id

    return redirect("/calendar")


@app.route("/logout")
def logout():
    """
    Logs the user out of the app and returns to the homepage

    Returns:
        Redirect: Sends user back to home
    """
    user_id = session.get("user_id")
    if user_id:
        delete_spotify_tokens(user_id)
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
    Renders the interactive calendar page with the active calendar's entries.
    The active calendar defaults to the user's personal calendar and can be
    changed via the calendar-switcher panel (/calendars/select).

    Returns:
        HTML: Renders calendar.html with user_notes data from table
    """
    user_id = session.get("user_id")
    calendar_id = get_active_calendar_id()

    notes_data = {}
    entries = get_all_by_calendar(calendar_id)
    if entries:
        for entry in entries:
            entry_date = entry.date.strftime("%Y-%m-%d")
            notes_data[entry_date] = {
                "text": entry.song_name,
                "artist": entry.artist_name,
                "spotify_link": entry.spotify_link,
                "song_image": entry.song_image,
                "notes": entry.journal_text,
                "location": entry.location_name,
                "is_owner": entry.user_id == user_id
            }

    active_calendar = get_calendar_by_id(calendar_id)

    return render_template(
        'calendar.html', subtitle='Calendar Page', text='This is the calendar page',
        user_notes=notes_data, active_calendar=active_calendar
    )


@app.route("/calendars")
@login_required
def list_calendars():
    """
    Returns the list of calendars (personal + shared) the current user
    belongs to, for the calendar-switcher panel.

    Returns:
        JSON: A list of calendar objects
    """
    user_id = session.get("user_id")
    active_id = get_active_calendar_id()
    calendars = get_user_calendars(user_id)

    data = [
        {
            "id": c.id,
            "name": c.name,
            "is_personal": c.is_personal,
            "is_active": c.id == active_id,
            "is_owner": c.owner_id == user_id,
            "join_code": c.join_code if c.owner_id == user_id else None
        }
        for c in calendars
    ]
    return jsonify(data)


@app.route("/calendars/select", methods=["POST"])
@login_required
def select_calendar():
    """
    Switches the active calendar for the current session

    Form Data:
        calendar_id (int): the calendar to switch to

    Returns:
        Redirect: Sends the user back to the calendar page
    """
    user_id = session.get("user_id")
    calendar_id = request.form.get("calendar_id", type=int)

    if calendar_id and is_calendar_member(user_id, calendar_id):
        session["active_calendar_id"] = calendar_id
    else:
        flash("You don't have access to that calendar.")

    return redirect(url_for('calendar'))


@app.route("/calendars/create", methods=["POST"])
@login_required
def create_shared_calendar():
    """
    Creates a new shared calendar owned by the current user and
    switches to it immediately

    Form Data:
        name (str): display name for the new calendar

    Returns:
        Redirect: Sends the user back to the calendar page
    """
    user_id = session.get("user_id")
    name = request.form.get("name", "").strip() or "Shared Calendar"

    calendar_obj = create_calendar(name=name, owner_id=user_id, is_personal=False)
    session["active_calendar_id"] = calendar_obj.id

    return redirect(url_for('calendar'))


@app.route("/calendars/join", methods=["POST"])
@login_required
def join_shared_calendar():
    """
    Joins an existing shared calendar using its invite code and
    switches to it immediately

    Form Data:
        code (str): the invite code for the calendar to join

    Returns:
        Redirect: Sends the user back to the calendar page
    """
    user_id = session.get("user_id")
    code = request.form.get("code", "")

    calendar_obj = join_calendar_by_code(user_id, code)

    if calendar_obj is None:
        flash("That invite code didn't match a calendar.")
        return redirect(url_for('calendar'))

    session["active_calendar_id"] = calendar_obj.id
    return redirect(url_for('calendar'))


@app.route("/calendars/delete", methods=["POST"])
@login_required
def delete_shared_calendar():
    """
    Deletes a shared calendar (and all of its entries/memberships).
    Only the calendar's owner may do this; personal calendars can't
    be deleted at all.

    Form Data:
        calendar_id (int): the calendar to delete

    Returns:
        Redirect: Sends the user back to the calendar page
    """
    user_id = session.get("user_id")
    calendar_id = request.form.get("calendar_id", type=int)

    if not calendar_id:
        return redirect(url_for('calendar'))

    was_active = session.get("active_calendar_id") == calendar_id
    success = delete_calendar(user_id, calendar_id)

    if not success:
        flash("Couldn't delete that calendar.")
    elif was_active:
        # bump them back to their personal calendar since the one
        # they were viewing no longer exists
        personal = get_or_create_personal_calendar(user_id)
        session["active_calendar_id"] = personal.id

    return redirect(url_for('calendar'))


@app.route("/on-this-day")
@login_required
def on_this_day():
    """
    Renders the on_this_day view that showcases the notes created
    by the user from past years on the same day and month.
    """

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for('spotify_login'))

    today = date.today()

    entries = get_all_by_user(user_id)

    if entries is None:
        entries = []
    
    # keeps track of memories from the same day and month
    memories = []

    for entry in entries:
        # check if entry has the same day and month as today 
        same_day = entry.date.day == today.day
        same_month = entry.date.month == today.month
        past_year = entry.date.year < today.year
    
        if same_day and same_month and past_year:
            memories.append(entry)
    
    memories = sorted(memories, key=lambda entry: entry.date, reverse=True)

    return render_template("on_this_day.html", today=today, memories=memories)
    


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
    mapbox_token = os.environ.get('MAPBOX_ACCESS_TOKEN')

    chosen_date = request.args.get('date')
    if not chosen_date:
        return redirect(url_for('calendar'))
    
    user_id = session.get("user_id", "test_user_1")
    if not user_id:
        return redirect(url_for('spotify_login'))

    calendar_id = get_active_calendar_id()

    date = datetime.strptime(chosen_date, '%Y-%m-%d').date()
    entry = get_by_date(calendar_id, date)

    if entry is None:
        return redirect(url_for('calendar'))

    note_data = {
        "song": entry.song_name,
        "photo": entry.photo_path, 
        "notes": entry.journal_text,
        "location": [entry.latitude, entry.longitude],
        "is_owner": entry.user_id == user_id
    }

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
        recs = s_generator.get_songs(entry.song_name, entry.journal_text, entry.location_name)

    # uses Spotify API to search Spotify for the songs from Gemini
    # load in spotify tokens from user
    token_data = get_spotify_tokens(user_id)
    songs = []
    saved_track_id = None

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
        saved_track_id = saved_results[0]['uri'].split(':')[-1] if saved_results else None

        for rec in recs:
            results = spotify.search_track(f"{rec['name']} {rec['artist']}")
            track_id = results[0]['uri'].split(':')[-1]
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

    note_data["track_id"] = saved_track_id

    lat = entry.latitude
    lng = entry.longitude

    return render_template('note.html', subtitle='Note page', text='This is the note page', 
    note=note_data, date = chosen_date, songs=songs,
    latitude=lat, longitude=lng, mapbox_token=mapbox_token)


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
    mapbox_token = os.environ.get('MAPBOX_ACCESS_TOKEN')

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

        calendar_id = get_active_calendar_id()

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

        # an entry already exists for this date in the active calendar -
        # only the person who created it is allowed to edit it
        existing_entry = get_by_date(calendar_id, entry_date)

        if existing_entry and existing_entry.user_id != user_id:
            flash("Only the person who created that day's entry can edit it.")
            return redirect(url_for('calendar'))

        if existing_entry:
            update_entry(user_id, existing_entry.id,
                song_name=song,
                artist_name=spotify_artist,
                spotify_link=spotify_uri,
                song_image=spotify_image,
                location_name=location,
                photo_path=file_path if filename else existing_entry.photo_path,
                journal_text=notes,
                latitude=lat,
                longitude=lng)
        else:
            add_entry(user=user_id,
                calendar=calendar_id,
                date=entry_date,
                song=song,
                artist=spotify_artist,
                link=spotify_uri,
                song_image=spotify_image,
                location=location,
                photo=filename,
                text=notes,
                latitude=lat,
                longitude=lng)


        return redirect(url_for('calendar'))

    return render_template('noteMaker.html', subtitle='Note-Maker page', text='This is the note-maker page', form=form, mapbox_token=mapbox_token)


@app.route("/note/delete", methods=["POST"])
@login_required
def delete_note():
    """
    Deletes an existing note entry (and its photo, if any) for the current user
    Only the original creator of the entry may delete it.

    Form Data:
        date (str): The date of the entry to delete, formatted 'YYYY-MM-DD'

    Returns:
        Redirect: Sends the user back to the calendar page
    """
    user_id = session.get("user_id")
    chosen_date = request.form.get("date")

    if not chosen_date:
        return redirect(url_for('calendar'))

    calendar_id = get_active_calendar_id()
    entry_date = datetime.strptime(chosen_date, '%Y-%m-%d').date()
    entry = get_by_date(calendar_id, entry_date)

    if entry is not None:
        if entry.user_id != user_id:
            flash("Only the person who created that day's entry can delete it.")
        else:
            delete_by_id(user_id, entry.id, upload_folder=app.config['UPLOAD_FOLDER'])

    return redirect(url_for('calendar'))

@app.route("/map")
@login_required
def map():
    """
    Renders the map page to see user's journal notes as location pins on the map

    Returns:
        HTML: Renders map.html
    """
    mapbox_token = os.environ.get('MAPBOX_ACCESS_TOKEN')

    return render_template('map.html', subtitle='Map page', text='This is the map page', mapbox_token=mapbox_token)

@app.route("/timeline")
@login_required
def timeline():
    """
    Renders the timeline page to see user's journal notes as a vertical timeline.
    Sorted from newest to oldest. User can choose to sort oldest to newest.

    Returns:
        HTML: Renders timeline.html
    """

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("spotify_login"))
    
    entries = get_all_by_user(user_id)

    # from the url we can get the sort query parameter
    sort_order = request.args.get("sort", "newest")

    if entries:
        if sort_order == "oldest":
            entries = sorted(entries, key=lambda entry: entry.date)
        else:
            entries = sorted(entries, key=lambda entry: entry.date, reverse=True)
    else:
        entries = []
    

    return render_template('timeline.html', subtitle='Timeline page', text='This is the timeline page', entries=entries, sort_order=sort_order)


@app.route("/entries/locations")
@login_required
def entry_locations():
    """
    Fetches location based entries in the active calendar to be rendered
    on the map. Ignores entries without a set latitude and longitude coordinate

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

    calendar_id = get_active_calendar_id()
    entries = get_all_by_calendar(calendar_id)
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


@app.route("/search-entries")
@login_required
def search_entries():
    """
    Searches the active calendar's journal entries for matches in song name,
    artist, location, or journal text.
    
    Query Parameters:
        q (str): The search keyword
        
    Returns:
        JSON: A list of matching entries with their dates and metadata
    """
    query = request.args.get("q", "").strip().lower()
    if not query:
        return jsonify([])

    user_id = session.get("user_id")
    if not user_id:
        return jsonify([])

    calendar_id = get_active_calendar_id()
    entries = get_all_by_calendar(calendar_id)
    if not entries:
        return jsonify([])

    results = []
    for entry in entries:
        # Check if the query matches the song name, artist, or date
        date_str = entry.date.strftime("%Y-%m-%d") if entry.date else ""
        song_match = query in (entry.song_name or "").lower()
        artist_match = query in (entry.artist_name or "").lower()

        date_match = query in date_str

        if song_match or artist_match or date_match: 
            results.append({
                "date": entry.date.strftime("%Y-%m-%d"),
                "song_name": entry.song_name,
                "artist_name": entry.artist_name,
                "location_name": entry.location_name,
                "song_image": entry.song_image
            })

    return jsonify(results)


@app.route("/update_server", methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo('/home/musicalmemories/Musical-Memories')
        origin = repo.remotes.origin
        origin.pull()
        return 'Updated PythonAnywhere successfully', 200
    else:
        return 'Wrong event type', 400


@app.route("/friends/request", methods=["POST"])
@login_required
def friend_request():
    """
    - Sends friend request from current user to given username
    - username (str): username of person being requested
    - Sends user back to their own profile page
    """
    user_id = session.get("user_id")
    username = request.form.get("username")

    target_user = get_user_by_username(username)
    if target_user is None:
        flash("User not found.")
        return redirect(url_for('profile', username=session.get("username")))
    
    success = send_request(user_id, target_user.id)
    if success:
        flash(f"Friend request sent to {username}!")
    else:
        flash("Could not send friend request.")

    return redirect(url_for('profile', username=session.get("username")))

@app.route("/friends/accept/<requester_username>", methods=["POST"])
@login_required
def friend_accept(requester_username):
    """
    - Accepts pending friend request from the given username
    - requester_username (str): username of person who sent request
    - Sends user back to their profile page
    """
    user_id = session.get("user_id")

    requester = get_user_by_username(requester_username)
    if requester is None:
        return redirect(url_for('calendar'))
    
    respond_to_request(requester.id, user_id, True)
    return redirect(url_for('profile', username=session.get("username")))

@app.route("/friends/decline/<requester_username>", methods=["POST"])
@login_required
def friend_decline(requester_username):
    """
    - Declines pending friend request from the given username
    - requester_username (str): username of person who sent request
    - Sends user back to their profile page
    """
    user_id = session.get("user_id")

    requester = get_user_by_username(requester_username)
    if requester is None:
        return redirect(url_for('calendar'))
    
    respond_to_request(requester.id, user_id, False)
    return redirect(url_for('profile', username=session.get("username")))

@app.route("/friends/cancel/<username>", methods=["POST"])
@login_required
def friend_cancel(username):
    """
    - Cancels pending friend request the current user sent to given username
    - Sends user back to their own profile page
    """
    user_id = session.get("user_id")

    target_user = get_user_by_username(username)
    if target_user is None:
        return redirect(url_for('calendar'))
    
    cancel_request(user_id, target_user.id)
    return redirect(url_for('profile', username=session.get("username")))

@app.route("/profile/<username>")
@login_required
def profile(username):
    """
    - Render's a user's profile page
    - username (str): username of the profile being viewed
    """
    user_id = session.get("user_id")

    target_user = get_user_by_username(username)
    if target_user is None:
        return redirect(url_for('calendar'))
    
    is_curr_user = target_user.id == user_id
    if not is_curr_user and not is_friend_of(user_id, target_user.id):
        return redirect(url_for('calendar'))
    
    entries = get_all_by_user(target_user.id)
    friends = get_friends(target_user.id) if is_curr_user else []
    pending_outbound = get_pending_outbound(target_user.id) if is_curr_user else []
    pending_inbound = get_pending_inbound(target_user.id) if is_curr_user else []

    return render_template('profile.html', subtitle='Profile Page', text='This is the profile page', viewing_user=target_user, is_curr_user=is_curr_user, entries=entries, friends=friends, pending_outbound=pending_outbound, pending_inbound=pending_inbound)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)