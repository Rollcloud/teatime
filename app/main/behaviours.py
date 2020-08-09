import re

from random import choice, sample

from .. import socketio
from . import agents, bots, lists


quotes = [
    "Be yourself; everyone else is already taken. -- Oscar Wilde",
    "Two things are infinite: the universe and human stupidity; and I'm not sure about the universe. -- Albert Einstein",
    "So many books, so little time. -- Frank Zappa",
    "Live as if you were to die tomorrow. Learn as if you were to live forever. -- Mahatma Gandhi",
    "A day without sunshine is like, you know, night. -- Steve Martin",
    "If you judge people, you have no time to love them. -- Mother Teresa",
    ]


class Behaviour:
    '''Create a parent class that provides bots with a certain behaviour'''

    def __init__(self, bot):
        self.bot = bot

    def perform(self):
        self.bot.speak(f"I'm sorry, I'm not able to {self.__class__.__name__}")


class Silent(Behaviour):
    def perform(self):
        self.bot.speak(f"Shhh...")


class Quote(Behaviour):
    def perform(self):
        for quote in sample(quotes, k=len(quotes)):
            self.bot.speak('<br>' + quote + '<br>')
            socketio.sleep(10)


class Wait(Behaviour):
    '''Blocking on a certain event and message combination being recieved'''

    def perform(self, event_name, message_key, start_word):
        event = None
        message = None
        while (
            event == event_name
            and message_key in message
            and message[message_key].startswith(start_word)
        ) is False:
            # check for last message
            try:
                event, message = self.bot.receive()
                socketio.sleep(0)

            except bots.NoNewMessagesException:  # no messages are available
                socketio.sleep(0.5)

        # wait over, expected message recieved
        return event, message


class Listen(Behaviour):
    def perform(self, event_name, message_key, start_word):
        while True:
            event, message = self.bot.receive()
            if (
                event == event_name
                and message_key in message
                and message[message_key].startswith(start_word)
            ) is False:
                # check the next message
                pass
            else:
                return event, message


class Rollcall(Behaviour):
    '''
    Each bot knows its order and annouces its position after
    the previous bot has annouced theirs'''

    def perform(self):
        from statemachine import StateMachine, State

        wait = Wait(self.bot)

        class RollCallMachine(StateMachine):
            active = State('Active', initial=True)
            locked = State('Locked')

            lock = active.to(locked)
            activate = locked.to(active)

        roll_call = RollCallMachine()

        triggers = lists.names + ['Rollcall']  # prevents infinite loops

        current_idx = triggers.index(self.bot.name)
        previous_name = triggers[current_idx - 1]
        next_name = triggers[current_idx + 1]

        while self.bot.is_alive:
            if roll_call.is_active:
                # wait for previous name
                wait.perform('message', 'msg', previous_name)

                # react to waiting
                self.bot.speak(self.bot.name)
                roll_call.lock()

            if roll_call.is_locked:
                # wait for previous name
                wait.perform('message', 'msg', next_name)

                # react to waiting
                roll_call.activate()

            socketio.sleep(1)


class Ehco(Behaviour):
    '''Repeat the last message, but scramble the middle letters'''

    def perform(self):
        xml_tags = re.compile('<.*?>')
        listen = Listen(self.bot)

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
                event, message = listen.perform('message', 'msg', '')

                # process found message
                text = re.sub(xml_tags, '', message['msg'])
                words = [scramble(word) for word in text.split()]
                self.bot.speak(' '.join(words))
                socketio.sleep(0.2)

            except bots.NoNewMessagesException:  # no messages are available
                socketio.sleep(2)


class Follow(Behaviour):
    '''Say nothing but follow its creator around'''

    def __init__(self, bot, target_token=None):
        self.target_token = target_token
        super().__init__(bot)

    def set_target(self, token):
        '''Set the target to follow'''
        self.target_token = token

    def perform(self):
        def sign(number):
            if number == 0:
                return 0

            return number / abs(number)

        def get_delta_pos_to(user):
            dx = user.pos_x - self.bot.pos_x
            dy = user.pos_y - self.bot.pos_y

            return dx, dy

        if self.target_token:  # if target is present

            # check target's position
            with self.bot.app.app_context():
                target = agents.get_user(self.target_token)

            dx, dy = get_delta_pos_to(target)
            # calculate distance to target
            # while distance is > 2
            # move closer to target
            while abs(dx) + abs(dy) > 2:
                # move in only one direction at a time
                move_vertically = sign(dx) == 0 or (
                    (sign(dy) != 0 and sign(dx) != 0) and choice([True, False])
                )
                if move_vertically:
                    self.bot.move(0, sign(dy))
                else:
                    self.bot.move(sign(dx), 0)

                socketio.sleep(0.3)
                # update target's position
                dx, dy = get_delta_pos_to(target)

        socketio.sleep(2)


class Puppy(Behaviour):
    def perform(self):
        """Behave like a (well-trained) puppy"""
        # when someone says '{name} come', follow that person
        # when that person says '{name} stay', stop following

        bot = self.bot
        listen = Listen(bot)
        follow = Follow(bot)

        while bot.is_alive:
            try:
                event, message = listen.perform('message', 'msg', bot.name)
                # identify sender
                sender = message['token']
                command = message['msg'].split(' ')[1]
                if command == 'come':
                    follow.set_target(sender)
                    bot.speak("Woof woof!")
                elif command == 'stay':
                    follow.set_target(None)
                    bot.speak("Woof!")

            except bots.NoNewMessagesException:  # no messages are available
                follow.perform()
                socketio.sleep(1)
