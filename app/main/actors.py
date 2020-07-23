import uuid


class Member:
    def __init__(self, token, name, emoji):
        """Create a new member. Members can join rooms."""
        self.token = token
        self.name = name
        self.emoji = emoji

    def __str__(self):
        return f"{self.token[:6]}({self.emoji} {self.name})"


class Area:
    def __init__(self, rid=None):
        """Create a new room."""
        self.rid = rid if rid else "R-" + str(uuid.uuid4())  # unique room-id
        self.name = self.rid[:8]
        self.members = {}

    def add_member(self, member):
        self.members[member.token] = member

    def remove_member(self, token):
        self.members.pop(token, None)
