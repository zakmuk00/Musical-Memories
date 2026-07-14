import unittest
import datetime
from flask import Flask
from database import db
from models import Entry, add_entry, get_by_date

class EntryTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        db.init_app(self.app)

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_add_entry(self):
        with self.app.app_context():
            test_date = datetime.date(2026, 7, 9)

            result = add_entry(user='test_user_1',
                                date=test_date,
                                song='bake shop',
                                artist='kuala',
                                link='https://open.spotify.com/track/2KU7CB4GA26r0VQ47Lvf9i',
                                song_image='https://i.scdn.co/image/ab67616d0000e1a3540c6a5c78bd857c85bb256d',
                                location='Molly Tea Bellevue',
                                text="They don't know I'm listening to peak fr.")
            self.assertTrue(result)
            print('Entry added')

            saved_entry = Entry.query.first()
            self.assertIsNotNone(saved_entry)
            print('Entry exists')
            self.assertEqual(saved_entry.song_name, 'bake shop')
            print('Song name matches')
            self.assertEqual(saved_entry.user_id, 'test_user_1')
            print('User id matches')
            self.assertEqual(saved_entry.date, test_date)
            print('Entry date matches')

    def test_get_by_date(self):
        with self.app.app_context():
            test_date = datetime.date(2026, 7, 9)

            dummy_entry = Entry(user_id='test_user_2',
                                date=test_date,
                                song_name='bake shop',
                                artist_name='kuala',
                                spotify_link='https://open.spotify.com/track/2KU7CB4GA26r0VQ47Lvf9i',
                                song_image='https://i.scdn.co/image/ab67616d0000e1a3540c6a5c78bd857c85bb256d',
                                location_name='Molly Tea Bellevue',
                                journal_text="They don't know I'm listening to peak fr.")
            db.session.add(dummy_entry)
            db.session.commit()

            valid_request = get_by_date('test_user_2', test_date)
            self.assertIsNotNone(valid_request)
            print('Entry found')
            self.assertEqual(valid_request.song_name, "bake shop")
            print('Song name matches')

            invalid_request = get_by_date('fake_user_id', test_date)
            self.assertIsNone(invalid_request)
            print('Fake entry not found')

if __name__ == '__main__':
    unittest.main()