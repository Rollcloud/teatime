import uuid

from random import choice
from pathlib import Path
from time import sleep

from flask import current_app
from flask_socketio import emit

from . import actors, areas, lists

p = Path('.')
q = p / 'app' / 'static' / 'quotes.txt'

with q.open() as f:
    quotes = f.read().split('\n\n')


class Bot(actors.Member):
    """A very basic, automonous chat-bot"""

    def __init__(self):
        token = "B" + uuid.uuid4().hex
        name = choice(lists.names)
        emoji = choice(lists.emojis)

        super().__init__(token, name, emoji)

    def start(self):
        print(f"{self}: Loading...")

        self.join_room('open')

        print(f"{self}: Ready and at your service!")

    def stop(self):
        print(f"{self}: Powering doowwwnnnn.....")

    def join_room(self, rid):
        print(f"{self}: Entering '{rid}'")
        self.rid = rid

        # self.rid =
        areas.add_member_to_area(areas, self, rid)

    def speak(self, words):
        print(f"{self}: I speak \"{words}\" to '{self.rid}'")
        emit('message', {'msg': self.name + ':' + words}, room=self.rid)

    def quote(self):
        message = choice(quotes)  # .replace('\n', '<br>')
        self.speak("<pre>" + message + "</pre>")


def run_bot(bot):
    bot.start()

    for each in range(10):
        print(f"{bot}: Brrrooop Barp!")
        bot.quote()
        sleep(6)

    bot.stop()
