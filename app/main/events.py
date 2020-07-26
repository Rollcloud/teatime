from flask import request, session, url_for
from flask_socketio import emit, join_room, leave_room, rooms

from .. import socketio
from . import agents
from . import bots


@socketio.on("connect", namespace="/chat")
def connect():
    token = session.get('token', '')
    name = session.get('name')
    avatar = session.get('emoji')

    if token == '':
        raise ConnectionRefusedError(f"Please login at: {url_for('.login')}")

    try:
        existing_user = agents.get_user(token)
        # keep pos_x and pos_y, replace all other attributes
        pos_x = existing_user.pos_x
        pos_y = existing_user.pos_y
    except KeyError as err:
        pos_x = 0
        pos_y = 0

    user = agents.User(token, name, avatar, pos_x, pos_y)
    print(f"⭐ - {user} connected")

    # forward new user message to all connected clients
    emit('user_joined', {'user': user.asdict()}, broadcast=True, include_self=False)

    agents.add_user(user)

    # send own token to this connector
    emit('identify', {'token': user.token})
    # send all currently connected users to this connector
    for user in agents.get_users():
        emit('user_joined', {'user': user.asdict()})


@socketio.on('text', namespace='/chat')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    token = session.get('token')
    user = agents.get_user(token)
    message = message['msg']

    # forward message to all connected clients
    emit(
        'message', {'msg': f"{user.handle}: {message}"}, broadcast=True
    )  # , room='optional'

    # special commands

    # create bot
    if message == "bot+":
        bot = bots.create_bot()
        emit('status', {'msg': f"{user.handle} created bot {bot}"}, broadcast=True)

    # kill bot
    elif message.startswith("bot-"):
        token_hint = message.split('bot-')[1]
        try:
            bots.destroy_bot(token_hint)
            emit('status', {'msg': f"{user.handle} killed bot {token}"}, broadcast=True)
        except KeyError as err:
            print(f"💥 Warning: {err}")


@socketio.on('move', namespace='/chat')
def move(delta):
    """Sent by a client character is moved.
    The message is sent to all people in the room."""
    token = delta['token']
    user = agents.get_user(token)
    user.pos_y += delta['y']
    user.pos_x += delta['x']

    response = {'token': token, 'pos_x': user.pos_x, 'pos_y': user.pos_y}

    # forward message to all connected clients
    emit('move', response, broadcast=True, include_self=False)


@socketio.on("disconnect", namespace="/chat")
def disconnect():
    token = session.get('token')
    user = agents.get_user(token)

    print(f"💢 - {user} disconnecting")

    # forward message to all connected clients
    emit('user_left', {'user': user.asdict()}, broadcast=True)
