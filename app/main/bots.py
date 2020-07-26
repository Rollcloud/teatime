import uuid

from pathlib import Path
from random import choice

from flask import current_app, session

from .. import socketio
from . import agents, lists

p = Path('.')
q = p / 'app' / 'static' / 'quotes.txt'

with q.open() as f:
    quotes = f.read().split('\n\n')


def create_client():
    # log the user in through Flask test client
    return current_app.test_client()


def upgrade_to_sio_client(test_client):
    # connect to Socket.IO without being logged in
    return socketio.test_client(namespace='/chat', flask_test_client=test_client)


class Behaviour:
    '''Create a parent class that provides bots with a certain behaviour'''

    pass


class Silence(Behaviour):
    pass


class Rollcall(Behaviour):
    '''
    Each bot knows its order and annouces its position after
    the previous bot has annouced theirs'''

    pass


class Ehco(Behaviour):
    '''Repeat the last message, but scramble the middle letters'''

    pass


class Bot(agents.User):
    """A very basic, automonous chat-bot"""

    is_alive = False

    def __init__(self):
        name = choice(lists.names)
        emoji = choice(lists.emojis)
        self.client = create_client()

        # login to create identity on server
        self.client.post(
            '/login', data=dict(name=name, emoji=emoji), follow_redirects=True,
        )
        token = session.get('token', '')
        name = session.get('name')

        super().__init__(token, name, emoji)

        self.behaviour = choice([Silence, Rollcall, Ehco])()

    def start(self):
        print(f"{self}: Loading...")

        self.client = upgrade_to_sio_client(self.client)

        if not self.client.is_connected:
            raise Exception(f"{self}: client not connected")

        self.is_alive = True

        print(f"{self}: Ready and at your service!")

    def stop(self):
        print(f"{self}: Powering doowwwnnnn.....")
        self.is_alive = False

    def join_room(self, rid):
        print(f"{self}: Entering '{rid}'")
        self.rid = rid
        join_room(rid)

        areas.add_member_to_area(self, rid)

    def speak(self, words):
        print(f"{self}: speaking to '{self.rid}'")
        emit('message', {'msg': self.handle + ':' + words})

    def quote(self):
        message = choice(quotes)  # .replace('\n', '<br>')
        self.speak("<pre>" + message + "</pre>")


def run_bot(bot):

    bot.start()

    # while bot.is_alive:
    #     print(f"{bot}: Brrrooop Barp!")
    #     bot.quote()
    #     sleep(6)

    # bot.stop()

    for each in range(10):
        print(f"{bot}: Brrrooop Barp!")
        bot.quote()
        # sleep(6)

    bot.stop()


def create_bot():
    bot = Bot()
    agents.add_user(bot)
    socketio.start_background_task(run_bot, bot)

    return bot


def destroy_bot(token_hint):
    users = current_app.users
    possible_tokens = [token for token in users.keys()]

    if len(possible_tokens) > 1:
        raise AmbiguousTokenException(f"multiple tokens match '{token_hint}'")

    bot = agents.remove_user(possible_tokens[0])
    bot.stop()

    return bot
