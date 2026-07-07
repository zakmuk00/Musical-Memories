from flask_sqlalchemy import SQLAlchemy

### Database Idea:
'''
Since we only have one entry per day, we don't need to have
two databases for the calendar and the entries

Possible Columns:
- Date (SQL Datatype)
- Song Name (VARCHAR)
- Spotify Link to the Song (VARCHAR)
- Link to Song/Album Image (VARCHAR)
- Journal Text (SQL TEXT)
- Some sort of map API data (TBD)
- Future: Scrapbooking data

Plan: 
- Make a SQLite database with one table
- Try making ORM functions so we can query directly to database
    without having to write SQL
'''

db = SQLAlchemy()



