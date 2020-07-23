from flask import current_app, request, session
from flask_socketio import emit, join_room, leave_room, rooms
from .. import executor, socketio

from . import actors, areas, bots


@socketio.on('joined_open', namespace='/chat')
def joined_open(message):
    """Sent by clients when they begin open conversations."""
    token = session.get('token')
    name = session.get('name')
    emoji = session.get('emoji')
    rid = 'open'

    member = actors.Member(token, name, emoji)

    join_room(rid)
    areas.add_member_to_area(member, rid)
    print(f"⭐ {member} joined {rid}")
    # if 'loudly' not in message or message['loudly']:
    #     emit('status', {'msg': name + ' has entered the open area.'}, room=rid)


@socketio.on('joined', namespace='/chat')
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    token = session.get('token')
    name = session.get('name')
    emoji = session.get('emoji')
    rid = session.get('room')

    member = actors.Member(token, name, emoji)

    join_room(rid)
    areas.add_member_to_area(member, rid)
    print(f"⭐ {member} joined {rid}")
    # emit('status', {'msg': f"{name} has entered the room '{rid[:6]}'."}, room=rid)


@socketio.on('text', namespace='/chat')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    name = session.get('name')
    rid = session.get('room')
    message = message['msg']

    # emit('message', {'msg': name + ':' + message}, room=rid)
    emit('message', {'msg': name + ':' + message}, room='open')

    # special commands

    # rename room
    if message.startswith("name:"):
        new_name = message.split("name:")[1]
        rename(rid, new_name)
        emit('status', {'msg': f"{name} renamed this room to '{new_name}'"}, room=rid)

    # create bot
    elif message == "bot+":
        bot = bots.Bot()
        executor.submit(bots.run_bot, bot)
        emit('status', {'msg': f"{name} created bot {bot}"}, room=rid)

    # kill bot
    elif message.startswith("bot-"):
        bid = message.split('bot-')[1]
        # terminate bot
        emit('status', {'msg': f"{name} killed bot {bid}"}, room=rid)


@socketio.on('left', namespace='/chat')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    token = session.get('token')
    name = session.get('name')
    rid = session.get('room')
    leave_room(rid)
    areas.remove_member_from_area(token, rid)
    # emit('status', {'msg': f"{name} has left the room '{rid[:6]}'."}, room=rid)


@socketio.on('left_open', namespace='/chat')
def left_open(message):
    """Sent by clients when they leave open conversation.
    A status message is broadcast to all people in the open area."""
    token = session.get('token')
    name = session.get('name')
    rid = 'open'
    leave_room(rid)
    areas.remove_member_from_area(token, rid)
    # emit('status', {'msg': name + ' has left the open area.'}, room=rid)


@socketio.on("disconnect", namespace="/chat")
def disconnect(message={}):
    token = session.get('token')
    name = session.get('name')
    print(f"⭐ {token[:6]}({name}) disconnecting")
    for rid in rooms(namespace="/chat"):
        if rid != request.sid:
            areas.remove_member_from_area(token, rid)
            # if 'loudly' not in message or message['loudly']:
            #     emit('status', {'msg': name + ' has left the room.'}, room=rid)
    # emit('status', {'msg': name + ' has disconnected.'})
