import os
from flask import Flask, render_template, url_for, request, redirect, jsonify
from datetime import datetime
from forms.noteMakerForm import NoteMakerForm
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config['SECRET_KEY'] = 'overly=secure-token-4-testin@' #change this when pushing to server

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
def note_maker():
    form = NoteMakerForm()

    if request.method == "GET":
        url_date = request.args.get('date')
        if url_date:
            form.date_created.data = url_date
        else:
            form.date_created.data = datetime.today().strftime('%Y-%m-%d')

    if form.validate_on_submit():
        photo_file = form.photo.data
        filename = None

        if photo_file:
            filename = secure_filename(photo_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo_file.save(file_path)
            #save to db here

        song = form.song.data
        location = form.location.data
        notes = form.notes.data
        chosen_date = form.date_created.data
        # Get user ID here and save both id and date to db
        return redirect(url_for('calendar'))
        
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
    app.run(host='0.0.0.0', port=5000, debug=True)
