from flask import current_app

from .. import executor
from . import bots


class AmbiguousTokenException(KeyError):
    pass


def add_member_to_people(member):
    people = current_app.people
    people[member.token] = member


def remove_member_from_people(token):
    try:
        people = current_app.people
        return people.pop(token, None)
    except KeyError:
        raise KeyError(f"token '{token[:6]}' does not exist")


def create_bot():
    bot = bots.Bot()
    add_member_to_people(bot)
    executor.submit(bots.run_bot, bot)

    return bot


def destroy_bot(token_hint):
    people = current_app.people
    possible_tokens = [token for token in people.keys()]

    if len(possible_tokens) > 1:
        raise AmbiguousTokenException(f"multiple tokens match '{token_hint}'")

    bot = remove_member_from_people(possible_tokens[0])
    bot.stop()

    return bot
