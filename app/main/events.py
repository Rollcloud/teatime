from flask import current_app, request, session, url_for

from .. import socketio
from . import agents
from . import behaviours
from . import lists


def new_user_joined(user):
    print(f"⭐ - {user} connected")

    # forward new user message to all other connected clients
    user.emit(
        'user_joined', {'user': user.asdict()}, broadcast=True, include_self=False
    )

    agents.add_user(user)

    # send own token to this connector
    user.emit('identify', {'token': user.token})
    # send all currently connected users to this connector
    for u in agents.get_users():
        user.emit('user_joined', {'user': u.asdict()})


def handle_text(user, message, recipients=None):
    if recipients:
        # forward message to all recipients
        user.emit('message', {'handle': user.handle, 'msg': message}, rooms=recipients)
    else:
        # forward message to all connected clients
        user.emit('message', {'handle': user.handle, 'msg': message}, broadcast=True)

    # special commands - only available to humans
    if type(user) == agents.User:

        # create bot
        if message == "bot+":
            bot = behaviours.create_bot(current_app, user.token)
            user.emit(
                'status', {'msg': f"{user.handle} created bot {bot}"}, broadcast=True
            )
            behaviours.run(bot)

        # create alphabots
        if message == "bot++":
            for name in lists.names:
                bot = behaviours.create_bot(
                    current_app, user.token, name=name, behaviour=behaviours.Rollcall
                )
                user.emit(
                    'status',
                    {'msg': f"{user.handle} created bot {bot}"},
                    broadcast=True,
                )
                behaviours.run(bot)

        # kill bot
        elif message.startswith("bot-"):
            token_hint = message.split('bot-')[1]
            try:
                bot = behaviours.destroy_bot(token_hint)
                user.emit(
                    'status',
                    {'msg': f"{user.handle} killed bot {bot.token}"},
                    broadcast=True,
                )
            except KeyError as err:
                print(f"💥 Warning: {err}")


def handle_move(user, delta):
    user.pos_y += delta['y']
    user.pos_x += delta['x']

    response = {'token': user.token, 'pos_x': user.pos_x, 'pos_y': user.pos_y}

    # forward message to all connected clients
    user.emit('move', response, broadcast=True, include_self=False)


def user_left(user):
    print(f"💢 - {user} disconnecting")

    agents.remove_user(user.token)

    # forward message to all connected clients
    user.emit('user_left', {'user': user.asdict()}, broadcast=True)


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
        pos_x = 20
        pos_y = 23
    user = agents.User(token, name, avatar, pos_x, pos_y, sid=request.sid)

    new_user_joined(user)


@socketio.on('text', namespace='/chat')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    token = session.get('token')
    user = agents.get_user(token)

    try:
        recipients = message['to']
    except KeyError:
        recipients = None
    message = message['msg']

    handle_text(user, message, recipients=recipients)


@socketio.on('move', namespace='/chat')
def move(delta):
    """Sent by a client character is moved.
    The message is sent to all people in the room."""
    token = delta['token']
    user = agents.get_user(token)

    handle_move(user, delta)


@socketio.on("disconnect", namespace="/chat")
def disconnect():
    token = session.get('token')
    user = agents.get_user(token)

    user_left(user)
