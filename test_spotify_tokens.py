from database import db
from models import SpotifyToken, save_spotify_tokens
from flask import Flask
from datetime import date

def start_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///models.db'
    db.init_app(app)

    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = start_app()
    with app.app_context():
        test_user_id = "test_user"

        token_data = {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_at": 9999999999.0
        }

        # test save tokens
        result = save_spotify_tokens(test_user_id, token_data)
        print("Save results: ", result)

          