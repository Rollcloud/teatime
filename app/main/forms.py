from flask_wtf import Form
from wtforms.fields import StringField, SubmitField
from wtforms.validators import Required


class LoginForm(Form):
    """Accepts a nickname."""

    name = StringField('Name', validators=[Required()])
    submit = SubmitField('Enter Open Area')
