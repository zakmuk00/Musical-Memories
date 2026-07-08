from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField,  TextAreaField, HiddenField
from wtforms.validators import Optional, Length

class NoteMakerForm(FlaskForm):
    song = StringField('Song', validators=[Optional(), Length(max=100)])
    location = StringField('location', validators=[Optional(), Length(max=150)])
    latitude = HiddenField('latitude', validators=[Optional()])
    longitude = HiddenField('longitude', validators=[Optional()])
    photo = FileField('Photo', validators=[
        Optional(),
        FileAllowed(['jpg','jpeg','png','pdf','gif'], 'images only')
    ])
    notes = TextAreaField('Notes')
    submit = SubmitField('Submit')