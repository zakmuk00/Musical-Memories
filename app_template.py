from database import db
from entry import Entry, add_entry, get_by_id, get_by_date, delete_by_id, delete_by_date, delete_table, update_entry
from flask import Flask
from datetime import date

def start_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///entries.db'
    db.init_app(app)

    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = start_app()
    with app.app_context():
        # normal new row
        sample_entry = Entry(date=date(2026, 7, 2),
                            song_name='Love, Fig', 
                            spotify_link='https://open.spotify.com/track/1UybzZ9Iag33eM0maYoqxC',
                            song_image='https://i.scdn.co/image/ab67616d0000e1a3ae75d2043f5d1a0f9ea7a9ef',
                            journal_text='I woke up to this song on shuffle, it was a great morning',
                            location_name='Home')
        db.session.add(sample_entry)
        db.session.commit()

        # new row with implemented method
        add_entry(date(2026, 7, 3), 
                    'Gangnam Style', 
                    'https://open.spotify.com/album/0ZjxizLeMyFEjR27JIvD99',
                    'https://i.scdn.co/image/ab67616d0000e1a36cfc57e5358c5e39e79bccbd',
                    'A true classic. Cant get enough of this honestly.',
                    'On a walk')

        # sample_entry_2 = Entry(date=date(2026, 7, 3),
        #                     song_name='Gangnam Style', 
        #                     spotify_link='https://open.spotify.com/album/0ZjxizLeMyFEjR27JIvD99',
        #                     song_image='https://i.scdn.co/image/ab67616d0000e1a36cfc57e5358c5e39e79bccbd',
        #                     journal_text='A true classic. Cant get enough of this honestly.',
        #                     location_name='On a walk')
        # db.session.add(sample_entry_2)
        get_by_id(1)
        get_by_id(3)
        get_by_date(7, 3, 2026)
        delete_by_id(1)
        update_entry(2, location_name='At a throwback party')

        # delete_table() # Deletes the entire table, might need this to avoid integrity erros while testing


        
    app.run(debug=True, use_reloader=False)