import re
import uuid

from collections import deque
from pathlib import Path
from random import choice, sample

from flask import session

from .. import socketio
from . import agents, events, lists
from .forms import LoginForm

p = Path('.')
q = p / 'app' / 'static' / 'quotes.txt'

with q.open() as f:
    quotes = f.read().split('\n\n')


class NoNewMessagesException(IndexError):
    pass


class Behaviour:
    '''Create a parent class that provides bots with a certain behaviour'''

    def __init__(self, bot):
        self.bot = bot

    def perform(self):
        self.bot.speak(f"I'm sorry, I'm not able to {self.__class__.__name__}")


class Silent(Behaviour):
    def perform(self):
        pass


class Quote(Behaviour):
    def perform(self):
        for each in range(6):
            message = choice(quotes)
            self.bot.speak('<br>' + message.replace('\n', '<br>') + '<br>')
            socketio.sleep(10)


class Rollcall(Behaviour):
    '''
    Each bot knows its order and annouces its position after
    the previous bot has annouced theirs'''

    def perform(self):
        current_idx = lists.names.index(self.bot.name)
        previous_name = lists.names[current_idx - 1]

        while self.bot.is_alive:
            try:
                event = None
                message = None
                while (
                    event == 'message'
                    and type(message) == dict
                    and 'msg' in message
                    and message['msg'] == previous_name
                ) is False:
                    # check for last message
                    event, message = self.bot.receive()
                    socketio.sleep(0.2)

                # process found message
                self.bot.speak(self.bot.name)
                socketio.sleep(0.2)

            except NoNewMessagesException:  # no messages are available
                socketio.sleep(1)


class Ehco(Behaviour):
    '''Repeat the last message, but scramble the middle letters'''

    def perform(self):
        xml_tags = re.compile('<.*?>')

        def scramble(word):
            # jumble middle letters
            if len(word) > 3:
                return (
                    word[:1]
                    + ''.join(sample(list(word[1:-1]), len(word[1:-1])))
                    + word[-1:]
                )
            else:
                return word

        while self.bot.is_alive:
            try:
                event = None
                while event != 'message':
                    # check for last message
                    event, message = self.bot.receive()
                    socketio.sleep(0.2)

                # process found message
                text = re.sub(xml_tags, '', message['msg'])
                words = [scramble(word) for word in text.split()]
                self.bot.speak(' '.join(words))
                socketio.sleep(0.2)

            except NoNewMessagesException:  # no messages are available
                socketio.sleep(2)


class Follow(Behaviour):
    '''Say nothing but follow its creator around'''

    def perform(self):
        def sign(number):
            if number == 0:
                return 0

            return number / abs(number)

        def get_delta_pos_to(user):
            dx = user.pos_x - self.bot.pos_x
            dy = user.pos_y - self.bot.pos_y

            return dx, dy

        while self.bot.is_alive:
            # check for creator's position
            with self.bot.app.app_context():
                creator = agents.get_user(self.bot.creator)

            dx, dy = get_delta_pos_to(creator)
            # calculate distance to creator
            # while distance is > 2
            # move closer to creator
            while abs(dx) + abs(dy) > 2:
                # move in only one direction at a time
                move_vertically = choice([True, False])
                if move_vertically:
                    self.bot.move(0, sign(dy))
                else:
                    self.bot.move(sign(dx), 0)

                socketio.sleep(0.5)
                # update creator's position
                dx, dy = get_delta_pos_to(creator)

            socketio.sleep(5)


class Bot(agents.User):
    """A very basic, automonous chat-bot"""

    is_alive = False

    def __init__(self, app, creator, name=None):
        name = name if name else choice(lists.names)
        emoji = choice(lists.emojis)
        token = uuid.uuid4().hex  # 32 hex-chars long

        self.messages = deque([])

        super().__init__(token, name, emoji, pos_x=21, pos_y=23)

        self.app = app
        self.creator = creator
        self.behaviour = Rollcall(self)
        # self.behaviour = choice([Silent, Quote, Rollcall, Ehco, Follow])(self)

    def send(self, event, message):
        self.messages.append((event, message))

    def receive(self):
        try:
            return self.messages.popleft()
        except IndexError as err:
            raise NoNewMessagesException(err)

    def start(self):
        print(f"{self}: Loading...")
        self.is_alive = True
        with self.app.app_context():
            events.new_user_joined(self)
        self.speak(f"Hello, I am a {self.behaviour.__class__.__name__}-bot")

    def stop(self):
        print(f"{self}: Powering doowwwnnnn.....")
        self.speak(f"B-bye, I'm off")
        with self.app.app_context():
            events.user_left(self)
        self.is_alive = False

    def speak(self, words):
        # print(f"{self}: speaking: \"{words[:20]}...\"")
        events.handle_text(self, words)

    def move(self, dx, dy):
        delta = {'x': dx, 'y': dy}
        events.handle_move(self, delta)


class NoTokenException(KeyError):
    pass


class AmbiguousTokenException(KeyError):
    pass


def bot_routine(bot):
    bot.start()
    bot.behaviour.perform()
    bot.stop()


def create_bot(current_app, creator, name=None):
    bot = Bot(current_app._get_current_object(), creator, name)
    agents.add_user(bot)

    return bot


def run(bot):
    socketio.start_background_task(bot_routine, bot)


def destroy_bot(token_hint):
    users = agents.get_users()
    possible_tokens = [
        user.token for user in users if user.token.startswith(token_hint)
    ]

    if len(possible_tokens) == 0:
        raise NoTokenException(f"no tokens match '{token_hint}'")

    if len(possible_tokens) > 1:
        raise AmbiguousTokenException(f"multiple tokens match '{token_hint}'")

    bot = agents.remove_user(possible_tokens[0])
    bot.is_alive = False

    return bot
