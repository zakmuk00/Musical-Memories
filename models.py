from database import db
import datetime
import os

# The ORM model of the entry
class Entry(db.Model):
    """
    This is the class that defines a journal entry in our app
    
    Note:
        There is a unique constraint to user_id and date.
        One user can only have one entry per day.

    Attributes:
        id (int): Auto-incremented unique Entry key
        user_id (str): Identifies who made the Entry
        date (date): The date of the journal Entry
        song_name (str): Name of the song
        spotify_link (str): Url to the song on Spotify
        song_image (str): Url to the song's image (recommend using Spotify api)
        photo_path (str): Path to the optional user photo
        journal_text (str): Optional journaling text written by user
        location_name (str): The location the journal entry was created
        latitude (num): latitude coordinate
        longitude (num): longitude coordinate
    """
    __tablename__ = 'calendar_entries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False)
    song_name = db.Column(db.String(255), nullable=False)
    spotify_link = db.Column(db.String(255), nullable=False)
    song_image = db.Column(db.String(255), nullable=False)
    location_name = db.Column(db.String(255), nullable=False)
    photo_path = db.Column(db.String(255))
    journal_text = db.Column(db.Text) # Optional
    # Need to make a backend route for this
    # journal_image = db.Column(db.String(255))
    latitude = db.Column(db.Float()) # Optional
    longitude = db.Column(db.Float()) # Optional
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='unique_user_date'),)

# Only accepts multiple parameters so far
# Might need another version where an Entry object can be passed
def add_entry(user, date, song, link, song_image, location, photo=None, text=None, latitude=None, longitude=None):
    """
    Adds a new entry into the database

    Args:
        user (str): The ID of the user creating the Entry
        date (date): The date the Entry is being created
        song (str): The name of the song
        link (str): Url to the song on Spotify
        image (str): Url to the song's image (recommend using Spotify api)
        location (str): The location the journal entry was created
        text (str): Journal Text
        latitude (num): latitude coordinate
        longitude (num): longitude coordinate

    Returns:
        bool: The status of adding the entry
    """
    # Validation needed
    if not type(date) is datetime.date:
        print('Wrong date format')
        return False
    
    if not (type(song) is str and type(link) is str and type(song_image) is str):
        print('Invalid song data')
        return False
    
    if not type(text) is str and text is not None:
        print('Invalid journal data')
        return False

    if not type(location) is str:
        print('Invalid location data')
        return False
    
    db.session.add(Entry(user_id=user,
                        date=date,
                        song_name=song,
                        spotify_link=link,
                        song_image=song_image,
                        location_name=location,
                        photo_path=photo,
                        journal_text=text,
                        latitude=latitude,
                        longitude=longitude))
    db.session.commit()
    return True

# Returns Entry object based on the id
# Only prints results for now, will return object later
def get_by_id(query_user_id, id):
    """
    Returns a Entry object based on the id
    
    Note: The current user id and the entry's user_id needs to match
    
    Args:
        query_user_id (str): The user id of entry being searched
        id (str): The id of the entry
    
    Returns:
        Entry: the Entry object if it exists and None otherwise
    """
    response = Entry.query.get(id)
    if response is None:
        print('Id not in table')
        print()
    elif response.user_id != query_user_id:
        print('User is not authorized for access')
        print()
        return None
    return response

def get_all_by_user(query_user_id):
    """
    Returns all the entries made by a user

    Args:
        query_user_id: The user id of entries being searched
    
    Returns:
        [Entry]: A list of entries made by the user
    """
    response = Entry.query.filter_by(user_id=query_user_id).all()
    if response is None:
        print('No entries by user')
    return response

def get_by_date(query_user_id, query_date):
    """
    Returns a Entry object based on the date created
    
    Note: The current user id and the entry's user_id needs to match
    
    Args:
        query_user_id (str): The user id of entry being searched
        query_date (date): The date of the entry
    
    Returns:
        Entry: the Entry object if it exists and None otherwise
    """
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
    """
    Deletes a Entry object based on the id
    
    Note: The current user id and the entry's user_id needs to match
    
    Args:
        query_user_id (str): The user id of entry being searched
        id (str): The id of the entry
    
    Returns:
        bool: The status of the deletion
    """
    response = Entry.query.filter_by(user_id=query_user_id, id=query_id).first()
    if response is not None:
        photo_path = response.photo_path
        db.session.delete(response)
        db.session.commit()
        if photo_path is not None:
            os.remove(photo_path)
            if os.path.exists(photo_path):
                print('Photo deletion failed')
            else:
                print('Photo deleted')

        print("Delete success")
        return True
    else:
        print("Deletion failed")
        return False

def delete_by_date(query_user_id, query_date):
    """
    Deletes an Entry based on the date created

    Note: The current user id and the entry's user_id needs to match

    Args:
        query_user_id (str): The user_id must match the id in Entry for access
        query_date (date): The date of the Entry being searched

    Returns:
        bool: The status of the deletion
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

# Use this when we update an entry and send all changes
# after clicking save button
# Documentations:
# hasattr: https://www.w3schools.com/python/ref_func_hasattr.asp
# setattr: https://www.w3schools.com/python/ref_func_setattr.asp
# getattr: https://www.w3schools.com/python/ref_func_getattr.asp
# kwargs: https://www.w3schools.com/python/python_args_kwargs.asp
# NOT FULLY TESTED YET
def update_entry(query_user_id, query_id, **kwargs):
    """
    Updates an existing entry with the passed fields

    Args:
        query_user_id: The user id of the Entry being searched
        id: The id of the Entry
        **kwargs: Fields being replaced (eg. location='Space Needle')
        (Refer to Entry documentation for list of fields)
    
    Returns:
        bool: The status of the update
    """
    entry = Entry.query.filter_by(user_id=query_user_id, id=query_id).first()
    if entry is None:
        print('Could not find entry')
        return False
    else:
        for key, value in kwargs.items():
            if key == 'id' or key == 'user_id':
                print(f'Key {key} is immutable, cannot update this field')
                continue
            if hasattr(entry, key):
                entry_value = getattr(entry, key)
                if entry_value == None or type(key) == type(entry_value):
                    setattr(entry, key, value)
                    print(f'{key} updated')
                else:
                    print(f'Type mismatch when updating {key}')
            else:
                print(f'{key} is not a valid key, did not update')
        db.session.commit()
        print("Change completed")
        return True

class SpotifyToken(db.Model):
    """
    Stores Spotify OAuth tokens for user 

    Note:
        This is seperate from Entry because tokens belong to each user not entry.

    Attributes:
        id (int): Auto-incremented primary key
        user_id (str): Identifies user
        access_token (str): hour long Spotify access token
        refresh_token (str): Long lived Spotify refresh token
        expires_at (float): timestamp for when access token expires
    """

    __tablename__ = 'spotify_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), nullable=False, unique=True)
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=False)
    expires_at = db.Column(db.Float, nullable=False)

def save_spotify_tokens(user_id, token_data):
    if not type(user_id) is str:
        print("Invalid user_id")
        return False
    
    if not type(token_data) is dict:
        print("Invalid token_data")
        return False
    
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_at = token_data.get("expires_at")

    if not access_token or not refresh_token or not expires_at:
        print("Missing Spotify token field")
        return False
    
    # need to check if the user already has tokens (query the db for existing token)
    existing = SpotifyToken.query.filter_by(user_id=user_id).first()

    # replace existing tokens with current tokens 
    if existing:
        existing.access_token = access_token
        existing.refresh_token = refresh_token
        existing.expires_at = expires_at
    
    # if user has no tokens, create a new object
    else:
        new_token = SpotifyToken(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )
        # insert new token object into database
        db.session.add(new_token)

    db.session.commit()
    print("Save success")
    return True

def get_spotify_tokens(user_id):
    token_row = SpotifyToken.query.filter_by(user_id=user_id).first()

    if token_row is None:
        print("No Spotify tokens found for user")
        return None
    


#def delete_spotify_tokens(user_id, token_data):
    


