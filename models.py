from database import db
from helpers import generate_username
import datetime
import os
import random
import string


# ---------------------------------------------------------------------------
# Calendar / CalendarMembership
# ---------------------------------------------------------------------------

class Calendar(db.Model):
    """
    A calendar is a container of Entries with a set of members.

    Every user gets exactly one personal calendar (is_personal=True),
    created automatically the first time they log in. Shared calendars
    are created explicitly and joined via a short invite code.

    Attributes:
        id (int): Auto-incremented unique Calendar key
        name (str): Display name (e.g. "My Calendar", "Me & Alex")
        owner_id (str): user_id of the calendar's creator
        is_personal (bool): True for a user's own default calendar
        join_code (str): Short code others can use to join (shared calendars only)
    """
    __tablename__ = 'calendars'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    owner_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=False)
    is_personal = db.Column(db.Boolean, default=False, nullable=False)
    join_code = db.Column(db.String(12), unique=True, nullable=True)


class CalendarMembership(db.Model):
    """
    Join table linking a User to a Calendar they can view/add to.

    Attributes:
        id (int): Auto-incremented unique key
        calendar_id (int): The Calendar being joined
        user_id (str): The User who is a member
    """
    __tablename__ = 'calendar_memberships'
    id = db.Column(db.Integer, primary_key=True)
    calendar_id = db.Column(db.Integer, db.ForeignKey('calendars.id'), nullable=False)
    user_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=False)
    __table_args__ = (
        db.UniqueConstraint(
            'calendar_id',
            'user_id',
            name='unique_calendar_member'
        ),
    )


def generate_join_code(length=6):
    """
    Generates a random alphanumeric invite code for a shared calendar
    """
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(random.choices(alphabet, k=length))


def create_calendar(name, owner_id, is_personal=False):
    """
    Creates a new Calendar and adds the owner as its first member

    Args:
        name (str): Display name for the calendar
        owner_id (str): user_id of the creator
        is_personal (bool): whether this is the user's default personal calendar

    Returns:
        Calendar: the newly created Calendar object
    """
    join_code = None if is_personal else generate_join_code()
    # extremely unlikely, but guard against a collision on the join code
    while join_code is not None and Calendar.query.filter_by(join_code=join_code).first():
        join_code = generate_join_code()

    calendar = Calendar(
        name=name,
        owner_id=owner_id,
        is_personal=is_personal,
        join_code=join_code
    )
    db.session.add(calendar)
    db.session.commit()

    db.session.add(CalendarMembership(calendar_id=calendar.id, user_id=owner_id))
    db.session.commit()

    return calendar


def get_or_create_personal_calendar(user_id):
    """
    Fetches a user's personal calendar, creating one if it doesn't exist yet

    Args:
        user_id (str): the user's id

    Returns:
        Calendar: the user's personal Calendar object
    """
    existing = Calendar.query.filter_by(owner_id=user_id, is_personal=True).first()
    if existing is not None:
        return existing
    return create_calendar(name="My Calendar", owner_id=user_id, is_personal=True)


def get_user_calendars(user_id):
    """
    Returns every Calendar the given user is a member of (personal + shared)

    Args:
        user_id (str): the user's id

    Returns:
        [Calendar]: list of Calendar objects, personal calendar first
    """
    memberships = CalendarMembership.query.filter_by(user_id=user_id).all()
    calendars = [Calendar.query.get(m.calendar_id) for m in memberships]
    calendars = [c for c in calendars if c is not None]
    calendars.sort(key=lambda c: (not c.is_personal, c.name.lower()))
    return calendars


def is_calendar_member(user_id, calendar_id):
    """
    Checks whether a user belongs to a given calendar

    Returns:
        bool: True if the user is a member of the calendar
    """
    if not calendar_id:
        return False
    response = CalendarMembership.query.filter_by(
        user_id=user_id, calendar_id=calendar_id).first()
    return response is not None


def join_calendar_by_code(user_id, code):
    """
    Adds a user to a shared calendar using its invite code

    Args:
        user_id (str): the user's id
        code (str): the invite code to look up

    Returns:
        Calendar: the joined Calendar, or None if the code was invalid
    """
    if not code:
        return None

    calendar = Calendar.query.filter_by(join_code=code.strip().upper()).first()
    if calendar is None:
        return None

    if not is_calendar_member(user_id, calendar.id):
        db.session.add(CalendarMembership(calendar_id=calendar.id, user_id=user_id))
        db.session.commit()

    return calendar


def get_calendar_by_id(calendar_id):
    """
    Returns a Calendar object based on the id
    """
    return Calendar.query.get(calendar_id)


def delete_calendar(user_id, calendar_id):
    """
    Deletes a shared calendar, along with every entry and membership
    that belongs to it.

    Note: only the calendar's owner may delete it, and personal
    calendars can never be deleted.

    Args:
        user_id (str): the user requesting the deletion
        calendar_id (int): the calendar to delete

    Returns:
        bool: True if the calendar was deleted
    """
    calendar_obj = Calendar.query.get(calendar_id)
    if calendar_obj is None:
        print('Calendar not found')
        return False

    if calendar_obj.is_personal:
        print('Cannot delete a personal calendar')
        return False

    if calendar_obj.owner_id != user_id:
        print('Only the owner can delete this calendar')
        return False

    Entry.query.filter_by(calendar_id=calendar_id).delete()
    CalendarMembership.query.filter_by(calendar_id=calendar_id).delete()
    db.session.delete(calendar_obj)
    db.session.commit()

    print('Calendar deleted')
    return True


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

# The ORM model of the entry
class Entry(db.Model):
    """
    This is the class that defines a journal entry in our app

    Note:
        There is a unique constraint on calendar_id and date.
        One calendar can only have one entry per day, regardless of
        which member created it. Only that member (user_id) may
        edit or delete it afterward.

    Attributes:
        id (int): Auto-incremented unique Entry key
        calendar_id (int): Identifies which Calendar the Entry belongs to
        user_id (str): Identifies who made the Entry (the only one who can edit it)
        date (date): The date of the journal Entry
        song_name (str): Name of the song
        artist_name (str): Name of the artist for the song
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
    calendar_id = db.Column(db.Integer, db.ForeignKey('calendars.id'), nullable=False)
    user_id = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False)
    song_name = db.Column(db.String(255), nullable=False)
    artist_name = db.Column(db.String(255), nullable=False)
    spotify_link = db.Column(db.String(255), nullable=False)
    song_image = db.Column(db.String(255), nullable=False)
    location_name = db.Column(db.String(255), nullable=False)
    photo_path = db.Column(db.String(255))
    journal_text = db.Column(db.Text)
    latitude = db.Column(db.Float())
    longitude = db.Column(db.Float())
    __table_args__ = (
        db.UniqueConstraint(
            'calendar_id',
            'date',
            name='unique_calendar_date'
            ),
        )


# Only accepts multiple parameters so far
# Might need another version where an Entry object can be passed
def add_entry(
        user, calendar, date, song, artist, link, song_image, location,
        photo=None, text=None, latitude=None, longitude=None
        ):
    """
    Adds a new entry into the database

    Args:
        user (str): The ID of the user creating the Entry
        calendar (int): The ID of the Calendar this Entry belongs to
        date (date): The date the Entry is being created
        song (str): The name of the song
        artist (str): The name of the artist
        link (str): Url to the song on Spotify
        image (str): Url to the song's image (recommend using Spotify api)
        location (str): The location the journal entry was created
        photo (str): The directory path to the image
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

    if not calendar:
        print('Missing calendar id')
        return False

    if not (
            type(song) is str and type(artist) is str
            ):
        if not (
                type(link) is str and type(song_image) is str
                ):
            print('Invalid song data')
            return False

    if not type(text) is str and text is not None:
        print('Invalid journal data')
        return False

    if not type(location) is str:
        print('Invalid location data')
        return False

    db.session.add(
        Entry(
            user_id=user,
            calendar_id=calendar,
            date=date,
            song_name=song,
            artist_name=artist,
            spotify_link=link,
            song_image=song_image,
            location_name=location,
            photo_path=photo,
            journal_text=text,
            latitude=latitude,
            longitude=longitude
        )
    )
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
    Returns all the entries made by a user, across every calendar
    they've contributed to

    Args:
        query_user_id: The user id of entries being searched

    Returns:
        [Entry]: A list of entries made by the user
    """
    response = Entry.query.filter_by(user_id=query_user_id).all()
    if response is None:
        print('No entries by user')
    return response


def get_all_by_calendar(calendar_id):
    """
    Returns all entries that belong to a given calendar, regardless
    of which member created them

    Args:
        calendar_id (int): The calendar being queried

    Returns:
        [Entry]: A list of entries in the calendar
    """
    response = Entry.query.filter_by(calendar_id=calendar_id).all()
    if response is None:
        print('No entries in calendar')
    return response


def get_by_date(calendar_id, query_date):
    """
    Returns the Entry for a given date within a given calendar
    (there is at most one, regardless of which member created it)

    Args:
        calendar_id (int): The calendar being searched
        query_date (date): The date of the entry

    Returns:
        Entry: the Entry object if it exists and None otherwise
    """
    response = Entry.query.filter_by(
        calendar_id=calendar_id,
        date=query_date).first()
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
def delete_by_id(query_user_id, query_id, upload_folder=None):
    """
    Deletes a Entry object based on the id

    Note: The current user id and the entry's user_id needs to match
    (only the original creator of an entry may delete it)

    Args:
        query_user_id (str): The user id of entry being searched
        id (str): The id of the entry

    Returns:
        bool: The status of the deletion
    """
    response = Entry.query.filter_by(
        user_id=query_user_id,
        id=query_id).first()
    if response is not None:
        photo_path = response.photo_path
        db.session.delete(response)
        db.session.commit()
        if photo_path is not None:
            full_path = os.path.join(
                upload_folder,
                photo_path) if upload_folder else photo_path
            try:
                os.remove(full_path)
                print('Photo deleted')
            except OSError as e:
                print(f'Photo deletion failed: {e}')

        print("Delete success")
        return True
    else:
        print("Deletion failed")
        return False


def delete_by_date(calendar_id, query_user_id, query_date):
    """
    Deletes an Entry based on the date created within a calendar

    Note: The current user id and the entry's user_id needs to match
    (only the original creator of an entry may delete it)

    Args:
        calendar_id (int): The calendar the Entry belongs to
        query_user_id (str): The user_id must match the id in Entry for access
        query_date (date): The date of the Entry being searched

    Returns:
        bool: The status of the deletion
    """
    response = Entry.query.filter_by(
        calendar_id=calendar_id,
        user_id=query_user_id,
        date=query_date
        ).first()
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

    Note: only the original creator of an entry (user_id) may update it

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
            if key in ('id', 'user_id', 'calendar_id'):
                print(f'Key {key} is immutable, cannot update this field')
                continue
            if hasattr(entry, key):
                entry_value = getattr(entry, key)
                if entry_value is None or type(key) == type(entry_value):
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
        This is seperate from Entry because tokens
        belong to each user not entry.

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
    """
    Saves new user tokens to the specified user id

    Args:
        user_id (str): The id of the user the tokens will be stored to
        token_data (obj): Spotify API's token data json for the user

    Returns:
        bool: The status of the saving
    """
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

    # need to check if the user already has tokens
    # (query the db for existing token)
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
    """
    Fetches recorded spotify tokens from the table for specified user

    Args:
        user_id (str): The user to fetch spotify tokens for

    Return:
        dict: The tokens of the user, None if user not found
    """
    token_row = SpotifyToken.query.filter_by(user_id=user_id).first()

    if token_row is None:
        print("No Spotify tokens found for user")
        return None

    return {
        "access_token": token_row.access_token,
        "refresh_token": token_row.refresh_token,
        "expires_at": token_row.expires_at
    }


# used if user logs out
def delete_spotify_tokens(user_id):
    """
    Deletes the stored spotify tokens for the specified user

    Args:
        user_id (str): The user to delete spotify tokens for
        token_data (obj):  Spotify API's token data json from the user
    """
    token_row = SpotifyToken.query.filter_by(user_id=user_id).first()

    if token_row is None:
        print("No Spotify tokens found to delete")

        return False
    db.session.delete(token_row)
    db.session.commit()
    return True


class User(db.Model):
    """
    This is the class that defines a user in our app

    id reuses the Spotify account id

    - id (str): Spotify account_id
    - username (str): unique handle that is used in profile URLs /profile/<username>
    - display_name (str): the name shown on the profile page
    - bio (str): an optional short bio text, kinda like Instagram
    """
    __tablename__ = 'users'
    id = db.Column(db.String(255), primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(150))
    bio = db.Column(db.Text)


def get_or_create_user(user_id, display_name):
    """
    Creates a User row for a given id if it doesn't exist or fetches if does exist.
    Also ensures the user has a personal calendar.
    """

    if not type(user_id) is str:
        print('Invalid user_id')
        return None

    existing = User.query.get(user_id)
    if existing is not None:
        get_or_create_personal_calendar(user_id)
        return existing

    db.session.add(User(id=user_id, username=generate_username(display_name), display_name=display_name))
    db.session.commit()
    print('User created')

    get_or_create_personal_calendar(user_id)

    return User.query.get(user_id)


def get_user_by_username(username):
    """
    Fetches a User based on username
    """
    response = User.query.filter_by(username=username).first()
    if response is None:
        print('Username does not exist in the table')
    return response


class Friendship(db.Model):
    """
    This is the class that defines a friendship between two users

    Friendship is a two-way accept: requester sends request, other
    person accepts or declines. A row can be either direction.

    - id (int): auto-incremented unique Friendship key
    - requester_id (str): user id of who sent the request
    - receiver_id (str): user id of who received request
    - status (str): 'pending', 'accepted', or 'declined'
    """
    __tablename__ = 'friendships'
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')


def is_friend_of(user1, user2):
    """
    Checks if two users are friends
    """
    response = Friendship.query.filter(
        db.or_(
            db.and_(
                Friendship.requester_id == user1,
                Friendship.receiver_id == user2
            ),
            db.and_(
                Friendship.requester_id == user2,
                Friendship.receiver_id == user1
            )
        ),
        Friendship.status == 'accepted'
    ).first()

    if response is not None:
        return True
    return False

def get_friends(user_id):
    """
    - Returns a list of User objects for all accepted friends of given user_id
    - Checks both directions
    """
    sent = Friendship.query.filter_by(requester_id=user_id, status='accepted').all()
    received = Friendship.query.filter_by(receiver_id=user_id, status='accepted').all()

    friends = []
    for f in sent:
        friend = User.query.get(f.receiver_id)
        if friend is not None:
            friends.append(friend)
    for f in received:
        friend = User.query.get(f.requester_id)
        if friend is not None:
            friends.append(friend)
    
    return friends

def send_request(requester_id, receiver_id):
    """
    Creates a pending friend request from the requester to the receiver
    """
    if not type(requester_id) is str or not type(receiver_id) is str:
        print('Invalid user id')
        return False
    if requester_id == receiver_id:
        print('Cannot send a friend request to yourself')
        return False
    
    existing = Friendship.query.filter(
        db.or_(
            db.and_(
                Friendship.requester_id == requester_id,
                Friendship.receiver_id == receiver_id
            ),
            db.and_(
                Friendship.requester_id == receiver_id,
                Friendship.receiver_id == requester_id
            )
        )
    ).first()
    if existing is not None:
        print('Friendship already exists or pending')
        return False
    
    db.session.add(
        Friendship(requester_id=requester_id, receiver_id=receiver_id, status='pending')
    )
    db.session.commit()
    
    print('Friend request sent')
    return True

def respond_to_request(requester_id, receiver_id, accept):
    """
    Accepts or declines a pending friend request,
    only receiver of request should call this.
    """
    if not type(accept) is bool:
        print('Invalid accept value, must be boolean')
        return False
    
    friendship = Friendship.query.filter_by(
        requester_id=requester_id,
        receiver_id=receiver_id,
        status='pending'
    ).first()

    if friendship is None:
        print('No pending request was found')
        return False
    if accept:
        friendship.status = 'accepted'
    else:
        friendship.status = 'declined'

    db.session.commit()
    print('Friend request has been updated')
    return True

def cancel_request(requester_id, receiver_id):
    """
    Cancels/revokes a pending friend request, only original requester should call this.
    """
    friendship = Friendship.query.filter_by(requester_id=requester_id, receiver_id=receiver_id, status='pending').first()
    if friendship is None:
        print('No pending request was found')
        return False
    
    db.session.delete(friendship)
    db.session.commit()
    print('Friend request cancelled')
    return True

def get_pending_outbound(user_id):
    """
    - Returns a list of User objects that user_id has sent pending requests to
    """
    sent = Friendship.query.filter_by(requester_id=user_id, status='pending').all()

    pending = []
    for f in sent:
        target = User.query.get(f.receiver_id)
        if target is not None:
            pending.append(target)
    
    return pending

def get_pending_inbound(user_id):
    """
    - Returns a list of User objects that have sent user_id a pending request
    """
    received = Friendship.query.filter_by(receiver_id=user_id, status='pending').all()

    pending = []
    for f in received:
        requester = User.query.get(f.requester_id)
        if requester is not None:
            pending.append(requester)
    
    return pending