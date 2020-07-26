from flask import redirect, render_template, request, session, url_for

from . import main
from .forms import LoginForm


@main.route('/')
def index():
    """Send the user to login if required or display the map"""
    token = session.get('token', '')
    if token == '':
        return redirect(url_for('.login'))
    else:
        name = session.get('name')
        avatar = session.get('emoji')
        return render_template('map.html', name=name, avatar=avatar)


@main.route('/login', methods=['GET', 'POST'])
def login():
    """Login form to enter the user's name."""
    form = LoginForm()
    if form.validate_on_submit():
        session['token'] = session.get('csrf_token')
        session['name'] = form.name.data
        session['emoji'] = form.emoji.data

        return redirect(url_for('.index'))

    elif request.method == 'GET':
        form.name.data = session.get('name', '')
        form.emoji.data = session.get('emoji', '👤')

    return render_template('login.html', form=form)


@main.route('/watering-hole')
def watering_hole():
    """The Watering Hole - the central meeting place.
    The user's token must be stored in the session."""
    token = session.get('token', '')
    name = session.get('name')
    avatar = session.get('emoji')
    if token == '':
        return redirect(url_for('.login'))

    return render_template('watering-hole.html', name=name, avatar=avatar)
