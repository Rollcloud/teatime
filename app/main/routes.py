from flask import current_app, session, redirect, url_for, render_template, request
from . import main
from .actors import Area, add_member_to_area
from .forms import LoginForm


@main.route('/', methods=['GET', 'POST'])
def index():
    """Login form to enter the user's name."""
    form = LoginForm()
    if form.validate_on_submit():
        session['token'] = "T" + session.get('csrf_token')
        session['name'] = form.name.data
        return redirect(url_for('.open'))
    elif request.method == 'GET':
        form.name.data = session.get('name', '')

    return render_template('index.html', form=form)


@main.route('/open')
def open():
    """All rooms. The user's name must be stored in the session."""
    token = session.get('token')
    name = session.get('name', '')
    if name == '':
        return redirect(url_for('.index'))

    _OPEN = 'open'
    # if open area does not yet exist, create it
    if _OPEN not in current_app.areas:
        current_app.areas[_OPEN] = Area(rid=_OPEN)
    session['room'] = add_member_to_area(current_app.areas, token, name, _OPEN)

    # trim areas list of empty rooms
    rooms = [area for area in list(current_app.areas.values())]
    return render_template('open.html', name=name, areas=rooms)


@main.route('/chat/new')
def chat_new():
    """Chat room. The user's name must be stored in the session."""
    return chat("")


@main.route('/chat/<rid>')
def chat(rid):
    """Chat room. The user's name must be stored in the session."""
    token = session.get('token')
    name = session.get('name', '')
    if name == '':
        return redirect(url_for('.index'))

    rid = add_member_to_area(current_app.areas, token, name, rid)
    session['room'] = rid
    return render_template('chat.html', name=name, room=rid)
