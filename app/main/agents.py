from flask import current_app
from flask_socketio import emit

from .. import socketio


class User:
    def __init__(self, token, name, avatar, pos_x, pos_y, sid=None):
        """Create a new user representing a unique client."""
        self.token = token
        self.name = name
        self.avatar = avatar
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.sid = sid

    def __str__(self):
        return f"{self.handle}({self.token[:6]})"

    def __getattr__(self, key):
        if key == 'handle':
            return f"{self.avatar} {self.name}"
        else:
            raise AttributeError(f"'User.{key}' is not defined")

    def asdict(self):
        return {
            'token': self.token,
            'name': self.name,
            'avatar': self.avatar,
            'pos_x': self.pos_x,
            'pos_y': self.pos_y,
        }

    def emit(self, event, message, broadcast=False, include_self=True, rooms=None):
        if type(self) == User:
            # if I am a User
            if broadcast:
                for u in get_users():
                    if include_self is True or (
                        include_self is False and self.token != u.token
                    ):
                        if type(u) == User:
                            # for other Users
                            emit(event, message, namespace="/chat", room=u.sid)
                        else:
                            # for other non-Users
                            u.send(event, message)
            elif rooms:
                # send to rooms
                for u in get_users():
                    if u.token in rooms or (
                        include_self is True and self.token == u.token
                    ):
                        if type(u) == User:
                            # for other Users
                            emit(event, message, namespace="/chat", room=u.sid)
                        else:
                            # for other non-Users
                            u.send(event, message)
            else:
                # send to self
                emit(event, message, namespace="/chat")
        else:
            # if I am a non-User
            if broadcast:
                with self.app.test_request_context("/"):
                    for u in get_users():
                        if self.token != u.token:  # DO NOT send to self
                            if type(u) == User:
                                # for other Users
                                socketio.emit(
                                    event, message, namespace="/chat", room=u.sid
                                )
                                socketio.sleep(0)
                            else:
                                # for other non-Users
                                u.send(event, message)
            elif rooms:
                # send to rooms
                with self.app.test_request_context("/"):
                    for u in get_users():
                        if (
                            u.token in rooms and self.token != u.token
                        ):  # DO NOT send to self
                            if type(u) == User:
                                # for other Users
                                socketio.emit(
                                    event, message, namespace="/chat", room=u.sid
                                )
                                socketio.sleep(0)
                            else:
                                # for other non-Users
                                u.send(event, message)
            else:
                # DO NOT send to self - prevents echo-bots from creating infinite loops
                pass


def add_user(user):
    users = current_app.users
    users[user.token] = user


def remove_user(token):
    try:
        users = current_app.users
        return users.pop(token, None)
    except KeyError:
        raise KeyError(f"token '{token[:6]}' does not exist")


def get_users():
    return list(current_app.users.values())


def get_user(token):
    users = current_app.users

    return users[token]
