from flask_wtf import FlaskForm
from wtforms.fields import HiddenField, StringField, SubmitField
from wtforms.validators import Required


class LoginForm(FlaskForm):
    """Accepts a nickname."""

    name = StringField('Name', validators=[Required()])
    emoji = HiddenField('Emoji', default="👤")
    submit = SubmitField('Enter')
