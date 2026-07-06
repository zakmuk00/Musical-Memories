from database import db
import datetime

# The ORM model of the entry
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

# Adds a new row into table
# Only accepts multiple parameters so far
# Might need another version where an Entry object can be passed
def add_entry(date, song, link, image, text, location):
    # Validation needed
    if not type(date) is datetime.date:
        print('Wrong date format')
        return
    
    if not (type(song) is str and type(link) is str and type(image) is str):
        print('Invalid song data')
        return
    
    if not type(text) is str:
        print('Invalid journal data')
        return

    if not type(location) is str:
        print('Invalid location data')
        return
    
    db.session.add(Entry(date=date, song_name=song, spotify_link=link, song_image=image, journal_text=text, location_name=location))
    db.session.commit()

# Returns Entry object based on the id
# Only prints results for now, will return object later
def get_by_id(id):
    response = Entry.query.get(id)
    if response is None:
        print('Id not in table')
        print()
    else:
        print('id:', response.id)
        print('song name:', response.song_name)
        print('created:', response.date)
        print()
        # return response

# Returns Entry object based on date in the format (mm, dd, yyyy)
# Parameters are nums and not strings
# Only prints results for now, will return object later
def get_by_date(month, day, year):
    # Validation needed
    query_date = datetime.date(year, month, day)
    response = Entry.query.filter_by(date=query_date).first()
    if response is None:
        print('Date not in table')
        print()
    else:
        print('id:', response.id)
        print('song name:', response.song_name)
        print('created:', response.date)
        print()
        # return response

# Deletes rows with the given id
# Returns boolean value of deletion status
def delete_by_id(id):
    response = Entry.query.get(id)
    if response is not None:
        db.session.delete(response)
        db.session.commit()
        print("Delete success")
        return True
    else:
        print("Deletion failed")
        return False

# Deletes rows with the given date in format (mm, dd, yyyy)
# Parameters are nums and not strings
# Returns boolean of deletion status
def delete_by_date(month, day, year):
    query_date = datetime.date(year, month, day)
    response = Entry.query.filter_by(date=query_date).first()
    if response is not None:
        db.session.delete(response)
        db.session.commit()
        print("Delete success")
        return True
    else:
        print("Deletion failed")
        return False

# Deletes the entire table
# Will not be that useful but good to have
def delete_table():
    Entry.query.delete()
    db.session.commit()
    print('Table deleted')