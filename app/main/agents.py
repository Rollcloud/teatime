import uuid

from flask import current_app


class AmbiguousTokenException(KeyError):
    pass


class User:
    def __init__(self, token, name, avatar, pos_x, pos_y):
        """Create a new user representing a unique client."""
        self.token = token
        self.name = name
        self.avatar = avatar
        self.pos_x = pos_x
        self.pos_y = pos_y

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
    return current_app.users.values()


def get_user(token):
    users = current_app.users

    return users[token]
