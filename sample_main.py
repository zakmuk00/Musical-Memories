from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

locations = []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/save-location", methods=["POST"])
def save_location():
    data = request.json
    locations.append(data)
    return jsonify({"status": "saved", "data": data})

@app.route("/locations")
def get_locations():
    return jsonify(locations)

if __name__ == "__main__":
    app.run(debug=True)
