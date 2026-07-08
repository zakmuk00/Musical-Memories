from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField,  TextAreaField, HiddenField
from wtforms.validators import Optional, Length, DataRequired

class NoteMakerForm(FlaskForm):
    song = StringField('Song', validators=[Optional(), Length(max=100)])
    location = StringField('location', validators=[Optional(), Length(max=150)])
    photo = FileField('Photo', validators=[
        Optional(),
        FileAllowed(['jpg','jpeg','png','pdf','gif'], 'images only')
    ])
    notes = TextAreaField('Notes')
    date_created = HiddenField('Date Created', validators=[DataRequired()])
    submit = SubmitField('Submit')