from flask import redirect, render_template, request, session, url_for
from . import main
from . import actors, areas
from .forms import LoginForm


@main.route('/')
def index():
    """Send the user to login if required"""
    name = session.get('name', '')
    if name == '':
        return redirect(url_for('.login'))
    else:
        return redirect(url_for('.watering_hole'))


@main.route('/login', methods=['GET', 'POST'])
def login():
    """Login form to enter the user's name."""
    form = LoginForm()
    if form.validate_on_submit():
        session['token'] = "T-" + session.get('csrf_token')
        session['name'] = form.name.data
        session['emoji'] = form.emoji.data
        return redirect(url_for('.watering_hole'))
    elif request.method == 'GET':
        form.name.data = session.get('name', '')
        form.emoji.data = session.get('emoji', '👤')

    return render_template('login.html', form=form)


@main.route('/watering-hole')
def watering_hole():
    """The Watering Hole - the central meeting place.
    The user's name must be stored in the session."""
    token = session.get('token')
    name = session.get('name', '')
    emoji = session.get('emoji', '')
    if name == '':
        return redirect(url_for('.login'))

    member = actors.Member(token, name, emoji)
    session['room'] = areas.add_member_to_open_area(member)

    live_areas = areas.list_areas()
    return render_template(
        'watering-hole.html', name=name, avatar=emoji, areas=live_areas
    )


@main.route('/chat/new')
def chat_new():
    """Chat room. The user's name must be stored in the session."""
    return chat("")


@main.route('/chat/<rid>')
def chat(rid):
    """Chat room. The user's name must be stored in the session."""

    token = session.get('token')
    name = session.get('name', '')
    emoji = session.get('emoji', '')
    if name == '':
        return redirect(url_for('.login'))

    member = actors.Member(token, name, emoji)
    rid = areas.add_member_to_area(member, rid)
    session['room'] = rid
    return render_template('chat.html', name=name, room=rid)
