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
        add_entry('user1',
                    date(2026, 7, 1),
                    'Love, Fig',
                    'https://open.spotify.com/track/1UybzZ9Iag33eM0maYoqxC',
                    'https://i.scdn.co/image/ab67616d0000e1a3ae75d2043f5d1a0f9ea7a9ef',
                    'Los Angeles, CA',
                    'I woke up to this song on shuffle, it was a great morning',
                    34.0522,
                    -118.2437)

        add_entry('user1',
                    date(2026, 7, 2),
                    'Gangnam Style',
                    'https://open.spotify.com/album/0ZjxizLeMyFEjR27JIvD99',
                    'https://i.scdn.co/image/ab67616d0000e1a36cfc57e5358c5e39e79bccbd',
                    'New York, NY',
                    'A true classic. Cant get enough of this honestly.',
                    40.7128,
                    -74.0060)

        add_entry('user1',
                    date(2026, 7, 3),
                    'Test Song Three',
                    'https://open.spotify.com/track/fake3',
                    'https://i.scdn.co/image/fake3',
                    'Chicago, IL',
                    'Another test entry.',
                    41.8781,
                    -87.6298)

        print("Added 3 test entries.")

    app.run(debug=True, use_reloader=False)