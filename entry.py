from database import db

class Entry(db.Model):
    __tablename__ = 'calendar_entries'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    song_name = db.Column(db.String(255), nullable=False)
    spotify_link = db.Column(db.String(255), nullable=False)
    song_image = db.Column(db.String(255), nullable=False)
    journal_text = db.Column(db.Text) # Optional
    location_name = db.Column(db.String(255), nullable=False)
    # latitude = db.Column(db.String(255)) # Optional
    # longitude = db.Column(db.String(255)) # Optional

def add_entry(date, song, link, image, text, location):
    # Validation needed
    db.session.add(Entry(date=date, song_name=song, spotify_link=link, song_image=image, journal_text=text, location_name=location))
    db.session.commit()
    
def get_by_id(id):
    # Validation needed
    return Entry.query.get(id)

def get_by_date(date):
    # Validation needed
    return Entry.query.filter_by(date=date).first()