from database import db
from entry import Entry
from flask import Flask

def start_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///entries.db'
    db.init_app(app)

    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = start_app()
    app.run(debug=True)