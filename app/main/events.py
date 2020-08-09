'''
Parses incoming socketio events and calls an action where appropiate
'''

from flask import request, session, url_for

from .. import socketio
from . import actions
from . import agents


@socketio.on("connect", namespace="/chat")
def connect():
    token = session.get('token', '')
    name = session.get('name')
    avatar = session.get('emoji')

    if token == '':
        raise ConnectionRefusedError(f"Please login at: {url_for('main.login')}")

    try:
        existing_user = agents.get_user(token)
        # keep pos_x and pos_y, replace all other attributes
        pos_x = existing_user.pos_x
        pos_y = existing_user.pos_y
    except KeyError as err:
        pos_x = 20
        pos_y = 23
    user = agents.User(token, name, avatar, pos_x, pos_y, sid=request.sid)

    actions.new_user_joined(user)


@socketio.on('text', namespace='/chat')
def text(data):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    token = session.get('token')
    user = agents.get_user(token)

    try:
        recipients = data['to']
    except KeyError:
        recipients = None
    message = data['msg']
    volume = data['volume'] if 'volume' in data else None

    actions.handle_text(user, message, recipients=recipients, volume=volume)


@socketio.on('move', namespace='/chat')
def move(delta):
    """Sent by a client character is moved.
    The message is sent to all people in the room."""
    token = delta['token']
    user = agents.get_user(token)

    actions.handle_move(user, delta)


@socketio.on("disconnect", namespace="/chat")
def disconnect():
    token = session.get('token')
    user = agents.get_user(token)

    actions.user_left(user)
