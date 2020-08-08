import uuid

from collections import deque
from random import choice

from .. import socketio
from . import actions, agents, lists


class BotException(Exception):
    pass


class BotHasExpiredException(BotException):
    pass


class NoNewMessagesException(BotException):
    pass


class Bot(agents.User):
    """A very basic autonomous agent"""

    is_alive = False

    def __init__(self, app, name=None, emoji=None):
        name = name if name else choice(lists.names)
        emoji = emoji if emoji else choice(lists.emojis)
        token = uuid.uuid4().hex  # 32 hex-chars long

        self.app = app

        super().__init__(token, name, emoji, pos_x=21, pos_y=23)

    def send(self, event, message):
        """Ignore incoming messages. To be implemented in subclasses."""
        pass

    def start(self):
        print(f"{self}: Loading...")
        self.is_alive = True
        with self.app.app_context():
            actions.new_user_joined(self)

    def stop(self):
        print(f"{self}: Powering doowwwnnnn.....")
        self.speak(f"B-bye, I'm off")
        with self.app.app_context():
            actions.user_left(self)
        self.is_alive = False

    def speak(self, words):
        if self.is_alive:
            # print(f"{self}: speaking: \"{words[:20]}...\"")
            actions.handle_text(self, words)
        else:
            raise BotHasExpiredException(f"{self} has ceased to be!")

    def move(self, dx, dy):
        if self.is_alive:
            delta = {'x': dx, 'y': dy}
            actions.handle_move(self, delta)
        else:
            raise BotHasExpiredException(f"{self} has ceased to be!")

    def perform(self):
        """Ignore requests to perform. To be implemented in subclasses."""
        pass


class CleverBot(Bot):
    def __init__(self, app, name=None, emoji=None, behaviour=None):

        self.behaviour = behaviour(self) if behaviour else None
        self.messages = deque([])

        super().__init__(app, name=name, emoji=emoji)

    def start(self):
        super().start()
        self.speak(f"Hello, I am a {self.behaviour.__class__.__name__}-bot")

    def send(self, event, message):
        """Store incoming messages"""
        self.messages.append((event, message))

    def receive(self):
        if self.is_alive:
            try:
                return self.messages.popleft()
            except IndexError as err:
                raise NoNewMessagesException(err)
        else:
            raise

    # def receive_all(self):
    #     if self.is_alive:
    #         if len(self.messages) > 0:
    #             messages = list(self.messages)
    #             self.messages.clear()

    #             return messages
    #         else:
    #             raise NoNewMessagesException(err)
    #     else:
    #         raise BotHasExpiredException(f"{self} has ceased to be!")

    def perform(self):
        """Act on assigned behaviours"""
        try:
            self.behaviour.perform()
        except BotHasExpiredException:
            pass
