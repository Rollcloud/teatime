from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField
from wtforms.validators import Required


class LoginForm(FlaskForm):
    """Accepts a nickname."""

    name = StringField('Name', validators=[Required()])
    submit = SubmitField('Enter Open Area')
