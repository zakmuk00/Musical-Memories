import random

def generate_username(display_name):
    """
    Turns a display name into a username, adding random
    digit(s) until unique.
    """
    from models import User
    
    if not display_name:
        display_name = 'user'
    default_username = display_name.lower().replace(' ', '')
    
    possible_name = default_username
    while User.query.filter_by(username=possible_name).first() is not None:
        possible_name = f"{possible_name}{random.randint(0, 9)}"
    
    return possible_name