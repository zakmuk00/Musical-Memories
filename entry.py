from database import db
import datetime

# The ORM model of the entry
class Entry(db.Model):
    """
    This is the class that defines a journal entry in our app
    Attributes:
        id (int): Auto-incremented unique Entry key
        user_id (str): Identified who made the Entry
        date (date): The date of the journal Entry
        song_name (str): Name of the song
        spotify_link (str): Url to the song on Spotify
        song_image (str): Url to the song's image (recommend using Spotify api)
        journal_text (str): Optional journaling text written by user
        location_name (str): The location the journal entry was created
    """
    __tablename__ = 'calendar_entries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False)
    song_name = db.Column(db.String(255), nullable=False)
    spotify_link = db.Column(db.String(255), nullable=False)
    song_image = db.Column(db.String(255), nullable=False)
    journal_text = db.Column(db.Text) # Optional
    # Need to make a backend route for this
    # journal_image = db.Column(db.String(255))
    location_name = db.Column(db.String(255), nullable=False)
    # latitude = db.Column(db.String(255)) # Optional
    # longitude = db.Column(db.String(255)) # Optional
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='unique_user_date'),)

# Adds a new row into table
# Only accepts multiple parameters so far
# Might need another version where an Entry object can be passed
def add_entry(user, date, song, link, image, text, location):
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
    
    db.session.add(Entry(user_id=user, date=date, song_name=song, spotify_link=link, song_image=image, journal_text=text, location_name=location))
    db.session.commit()

# Returns Entry object based on the id
# Only prints results for now, will return object later
def get_by_id(query_user_id, id):
    response = Entry.query.get(id)
    if response is None:
        print('Id not in table')
        print()
        return None
    elif response.user_id != query_user_id:
        print('User is not authorized for access')
        print()
        return None
    else:
        return response

def get_all_by_user(query_user_id):
    response = Entry.query.filter_by(user_id=query_user_id).all()
    if response is None:
        print('No entries by user')
    return response

# Returns Entry object based on date in the format (mm, dd, yyyy)
# Parameters are nums and not strings
# Only prints results for now, will return object later
def get_by_date(query_user_id, query_date):
    # Validation needed
    response = Entry.query.filter_by(user_id=query_user_id, date=query_date).first()
    if response is None:
        print('Date not in table')
        print()
    else:
        print('id:', response.id)
        print('song name:', response.song_name)
        print('created:', response.date)
        print()
        return response

# Deletes rows with the given id
# Returns boolean value of deletion status
def delete_by_id(query_user_id, query_id):
    response = Entry.query.filter_by(user_id=query_user_id, id=query_id).first()
    if response is not None:
        db.session.delete(response)
        db.session.commit()
        print("Delete success")
        return True
    else:
        print("Deletion failed")
        return False

def delete_by_date(query_user_id, query_date):
    """
    Deletes an Entry based on the date created
    Args:
        query_user_id (str): The user_id must match the id in Entry for access
        query_date (date): The date of the Entry being searched
    Returns:
        bool: The status of deletion
    """
    response = Entry.query.filter_by(user_id=query_user_id, date=query_date).first()
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

# Updates an existing entry
# Use this when we update an entry and send all changes
# after clicking save button
# Documentations:
# hasattr: https://www.w3schools.com/python/ref_func_hasattr.asp
# setattr: https://www.w3schools.com/python/ref_func_setattr.asp
# kwargs: https://www.w3schools.com/python/python_args_kwargs.asp
# NOT FULLY TESTED YET
def update_entry(query_user_id, id, **kwargs):
    entry = Entry.query.filter_by(user_id=query_user_id, id=id).first()
    if entry is None:
        print('Could not find entry')
        return False
    else:
        for key, value in kwargs.items():
            if hasattr(entry, key):
                # Vulnerability: No type checking yet
                setattr(entry, key, value)
                print(f'{key} updated')
            else:
                print(f'{key} is not a valid key, did not update')
        
        db.session.commit()
        print("Change completed")
        return True