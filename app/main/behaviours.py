import re

from collections import deque
from pathlib import Path
from random import choice, sample

from .. import socketio
from . import agents, bots, lists

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
        from statemachine import StateMachine, State

        class RollCallMachine(StateMachine):
            active = State('Active', initial=True)
            locked = State('Locked')

            lock = active.to(locked)
            activate = locked.to(active)

        roll_call = RollCallMachine()

        current_idx = lists.names.index(self.bot.name)
        previous_name = lists.names[current_idx - 1]
        try:
            next_name = lists.names[current_idx + 1]
        except IndexError:
            # for the last name on the list, use the first index
            next_name = lists.names[0]

        while self.bot.is_alive:
            try:
                event = None
                message = None

                if roll_call.is_active:
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
                    roll_call.lock()

                if roll_call.is_locked:
                    while (
                        event == 'message'
                        and type(message) == dict
                        and 'msg' in message
                        and message['msg'] == next_name
                    ) is False:
                        # check for last message
                        event, message = self.bot.receive()
                        socketio.sleep(0.2)

                    # process found message
                    roll_call.activate()

                socketio.sleep(1)

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


class CleverBot(bots.Bot):
    def __init__(self, app, creator, name=None, behaviour=None):

        self.creator = creator
        self.behaviour = (
            behaviour(self)
            if behaviour
            else choice([Ehco, Follow, Quote, Rollcall, Silent])(self)
        )

        self.messages = deque([])

        super().__init__(app, name=name)

    def send(self, event, message):
        """Store incoming messages"""
        self.messages.append((event, message))

    def receive(self):
        try:
            return self.messages.popleft()
        except IndexError as err:
            raise NoNewMessagesException(err)

    def perform(self):
        """Act on assigned behaviours"""
        self.behaviour.perform()


def create_bot(current_app, creator, name=None, behaviour=None):
    bot = CleverBot(current_app._get_current_object(), creator, name, behaviour)
    agents.add_user(bot)

    return bot


# convenience functions
def run(bot):
    return bots.run(bot)


def destroy_bot(token_hint):
    return bots.destroy_bot(token_hint)
