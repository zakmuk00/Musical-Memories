from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField,  TextAreaField, HiddenField
from wtforms.validators import Optional, Length, DataRequired

class NoteMakerForm(FlaskForm):
    song = StringField('Song', validators=[Optional(), Length(max=100)])
    spotify_uri = HiddenField('Spotify URI', validators=[Optional()])
    spotify_artist = HiddenField('Spotify Artist', validators=[Optional()])
    spotify_image = HiddenField('Spotify Image', validators=[Optional()])
    location = StringField('location', validators=[Optional(), Length(max=150)])
    latitude = HiddenField('latitude', validators=[Optional()])
    longitude = HiddenField('longitude', validators=[Optional()])
    photo = FileField('Photo', validators=[
        Optional(),
        FileAllowed(['jpg','jpeg','png','pdf','gif'], 'images only')
    ])
    notes = TextAreaField('Notes')
    date_created = HiddenField('Date Created', validators=[DataRequired()])
    submit = SubmitField('Submit')