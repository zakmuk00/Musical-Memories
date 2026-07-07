from flask import Flask, request, jsonify, render_template, url_for
app = Flask(__name__)

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

@app.route("/note")
def note():
    return render_template('note.html', subtitle='Note page', text='This is the note page')

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
