from database import db

class Entry(db.Model):
    __tablename__ = 'calendar_entries'
    
    date = db.Column(db.Date, unique=True, primary_key=True, nullable=False)
    song_name = db.Column(db.String(255), nullable=False)
    spotify_link = db.Column(db.String(255), nullable=False)
    song_image = db.Column(db.String(255), nullable=False)
    journal_text = db.Column(db.Text)
    # latitude = db.Column(db.Integer)
    # longitude = db.Column(db.Integer)