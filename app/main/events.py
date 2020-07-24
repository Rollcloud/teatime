from flask import current_app, request, session
from flask_socketio import emit, join_room, leave_room, rooms
from .. import socketio

from . import actors, areas, people


@socketio.on("connect", namespace="/chat")
def connect(message={}):
    token = session.get('token')
    name = session.get('name')
    emoji = session.get('emoji')

    member = actors.Member(token, name, emoji)
    people.add_member_to_people(member)

    print(f"⭐ {member} connected")


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
    print(f"✳️  {member} joined {rid}")
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
    print(f"✳️  {member} joined {rid}")
    # emit('status', {'msg': f"{name} has entered the room '{rid[:6]}'."}, room=rid)


@socketio.on('text', namespace='/chat')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    token = session.get('token')
    rid = session.get('room')
    message = message['msg']
    member = current_app.people[token]

    # emit('message', {'msg': name + ':' + message}, room=rid)
    emit('message', {'msg': member.handle + ': ' + message}, room='open')

    # special commands

    # rename room
    if message.startswith("name:"):
        new_name = message.split("name:")[1]
        rename(rid, new_name)
        emit(
            'status',
            {'msg': f"{member.handle} renamed this room to '{new_name}'"},
            room=rid,
        )

    # create bot
    elif message == "bot+":
        bot = people.create_bot()
        emit('status', {'msg': f"{member.handle} created bot {bot}"}, room=rid)

    # kill bot
    elif message.startswith("bot-"):
        token = message.split('bot-')[1]
        try:
            people.destroy_bot(token)
            emit('status', {'msg': f"{member.handle} killed bot {token}"}, room=rid)
        except KeyError as err:
            print(f"💥 Warning: {err}")


@socketio.on('left', namespace='/chat')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    people = current_app.people
    token = session.get('token')
    rid = session.get('room')
    leave_room(rid)
    member = people[token]
    areas.remove_member_from_area(token, rid)
    # emit('status', {'msg': f"{name} has left the room '{rid[:6]}'."}, room=rid)
    print(f"❎ {member} left {rid}")


@socketio.on('left_open', namespace='/chat')
def left_open(message):
    """Sent by clients when they leave open conversation.
    A status message is broadcast to all people in the open area."""
    people = current_app.people
    token = session.get('token')
    rid = 'open'
    leave_room(rid)
    member = people[token]
    areas.remove_member_from_area(token, rid)
    # emit('status', {'msg': name + ' has left the open area.'}, room=rid)
    print(f"❎ {member} left {rid}")


@socketio.on("disconnect", namespace="/chat")
def disconnect(message={}):
    token = session.get('token')
    name = session.get('name')
    print(f"💢 {token[:6]}({name}) disconnecting")
    for rid in rooms(namespace="/chat"):
        if rid != request.sid:
            areas.remove_member_from_area(token, rid)
            # if 'loudly' not in message or message['loudly']:
            #     emit('status', {'msg': name + ' has left the room.'}, room=rid)
    # emit('status', {'msg': name + ' has disconnected.'})
