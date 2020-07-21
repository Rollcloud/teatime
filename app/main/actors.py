import uuid


class Member:
    def __init__(self, token, name):
        """Create a new member. Members can join rooms."""
        self.token = token
        self.name = name


class Area:
    def __init__(self, rid=None):
        """Create a new room."""
        self.rid = rid if rid else "R" + str(uuid.uuid4())  # unique room-id
        self.name = self.rid[:8]
        self.members = {}

    def add_member(self, member):
        self.members[member.token] = member

    def remove_member(self, token):
        self.members.pop(token, None)


def add_member_to_area(areas, token, member_name, rid):
    print(f"⭐ Adding {token[:6]}({member_name}) to {rid}")
    member = Member(token, member_name)
    try:
        areas[rid].add_member(member)
        return rid
    except KeyError:
        # if area does not yet exist, create it
        area = Area()
        areas[area.rid] = area
        areas[area.rid].add_member(member)
        return area.rid
