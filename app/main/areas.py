from flask import current_app

from . import actors


def add_member_to_area(member, rid):
    print(f"⭐ Adding {member} to {rid}")
    areas = current_app.areas
    try:
        areas[rid].add_member(member)
        return rid
    except KeyError:
        # if area does not yet exist, create it
        area = actors.Area()
        areas[area.rid] = area
        areas[area.rid].add_member(member)
        return area.rid


def add_member_to_open_area(member):
    _OPEN = 'open'
    # if open area does not yet exist, create it
    if _OPEN not in current_app.areas:
        current_app.areas[_OPEN] = actors.Area(rid=_OPEN)

    return add_member_to_area(member, _OPEN)


def remove_member_from_area(token, rid):
    print(f"⭐ Removing {token[:6]} from {rid}")
    areas = current_app.areas
    try:
        areas[rid].remove_member(token)
    except KeyError:
        print(f"💥 Warning: room '{rid}' does not exist")
        return
    if len(areas[rid].members) <= 0:
        areas.pop(rid, None)


def rename(rid, new_name):
    current_app.areas[rid].name = new_name


def list_areas():
    return [area for area in list(current_app.areas.values())]
