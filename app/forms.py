'''  
Summary:
- Defined Flask-WTF forms for the admin and user-facing features:
  * LoginForm for admin authentication
  * QuestionForm for creating/updating quiz questions
  * ImageUploadForm for handling both traffic sign and custom quiz-image uploads
  * SQLConsoleForm for executing raw SQL within the admin panel

This forms.py will be used in app/admin/routes.py (and potentially other blueprints) to validate and process incoming form data.  
'''
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, FileField, SubmitField
from wtforms.validators import DataRequired, Length, AnyOf

class LoginForm(FlaskForm):
    username = StringField('Brukernavn', validators=[DataRequired(), Length(min=3, max=100)])
    password = PasswordField('Passord', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Logg inn')

class QuestionForm(FlaskForm):
    question = TextAreaField('Spørsmål', validators=[DataRequired(), Length(max=500)])
    option_a = StringField('Alternativ A', validators=[DataRequired(), Length(max=200)])
    option_b = StringField('Alternativ B', validators=[DataRequired(), Length(max=200)])
    option_c = StringField('Alternativ C', validators=[DataRequired(), Length(max=200)])
    option_d = StringField('Alternativ D', validators=[DataRequired(), Length(max=200)])
    correct_option = SelectField(
        'Riktig svar',
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')],
        validators=[DataRequired(), AnyOf(['a', 'b', 'c', 'd'])]
    )
    category = StringField('Kategori', validators=[Length(max=100)])
    image_filename = SelectField('Bilde', choices=[], coerce=str)
    submit = SubmitField('Lagre spørsmål')

class ImageUploadForm(FlaskForm):
    image = FileField('Velg bildefil', validators=[DataRequired()])
    folder = SelectField(
        'Mappe',
        choices=[('signs', 'Traffic Signs'), ('quiz', 'Quiz Images')],
        validators=[DataRequired()]
    )
    # Only relevant when folder == 'signs'
    sign_code = StringField('Skiltkode', validators=[Length(max=50)])
    name = StringField('Skiltnavn', validators=[Length(max=100)])
    description = TextAreaField('Beskrivelse', validators=[Length(max=300)])

    # Only relevant when folder != 'signs'
    title = StringField('Tittel', validators=[Length(max=150)])
    description_quiz = TextAreaField('Quiz-beskrivelse', validators=[Length(max=300)])

    submit = SubmitField('Last opp bilde')

class SQLConsoleForm(FlaskForm):
    sql_query = TextAreaField('SQL-spørring', validators=[DataRequired(), Length(max=10000)])
    submit = SubmitField('Kjør')
