from flask import current_app, request, session
from flask_socketio import emit, join_room, leave_room, rooms
from .. import socketio

from . import actors


def remove_member_from_area(token, rid):
    print(f"⭐ Removing {token[:6]}({session.get('name')}) from {rid}")
    areas = current_app.areas
    try:
        areas[rid].remove_member(token)
    except KeyError:
        print(f"💥 Warning: room '{rid}' does not exist")
        return
    if len(areas[rid].members) <= 0:
        areas.pop(rid, None)


@socketio.on('joined_open', namespace='/chat')
def joined_open(message):
    """Sent by clients when they begin open conversations."""
    token = session.get('token')
    name = session.get('name')
    rid = 'open'
    print(f"⭐ {token[:6]}({name}) joined {rid}")
    join_room(rid)
    actors.add_member_to_area(current_app.areas, token, name, rid)
    # if 'loudly' not in message or message['loudly']:
    #     emit('status', {'msg': name + ' has entered the open area.'}, room=rid)


@socketio.on('joined', namespace='/chat')
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    token = session.get('token')
    name = session.get('name')
    rid = session.get('room')
    print(f"⭐ {token[:6]}({name}) joined {rid}")
    join_room(rid)
    actors.add_member_to_area(current_app.areas, token, name, rid)
    emit('status', {'msg': f"{name} has entered the room '{rid[:6]}'."}, room=rid)


@socketio.on('text', namespace='/chat')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    name = session.get('name')
    rid = session.get('room')
    message = message['msg']
    # rename room
    if message.startswith("name:"):
        new_name = message.split("name:")[1]
        current_app.areas[rid].name = new_name
        emit('status', {'msg': f"'{name}' renamed this room to '{new_name}'"}, room=rid)

    else:
        # emit('message', {'msg': name + ':' + message}, room=rid)
        emit('message', {'msg': name + ':' + message}, room='open')


@socketio.on('left', namespace='/chat')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    token = session.get('token')
    name = session.get('name')
    rid = session.get('room')
    leave_room(rid)
    remove_member_from_area(token, rid)
    emit('status', {'msg': f"{name} has left the room '{rid[:6]}'."}, room=rid)


@socketio.on('left_open', namespace='/chat')
def left_open(message):
    """Sent by clients when they leave open conversation.
    A status message is broadcast to all people in the open area."""
    token = session.get('token')
    name = session.get('name')
    rid = 'open'
    leave_room(rid)
    remove_member_from_area(token, rid)
    # emit('status', {'msg': name + ' has left the open area.'}, room=rid)


@socketio.on("disconnect", namespace="/chat")
def disconnect(message):
    token = session.get('token')
    name = session.get('name')
    print(f"⭐ {token[:6]}({name}) disconnecting")
    for rid in rooms(namespace="/chat"):
        if rid != request.sid:
            remove_member_from_area(token, rid)
            if 'loudly' not in message or message['loudly']:
                emit('status', {'msg': name + ' has left the room.'}, room=rid)
    # emit('status', {'msg': name + ' has disconnected.'})
