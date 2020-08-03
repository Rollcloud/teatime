import uuid

from random import choice

from .. import socketio
from . import agents, events, lists


class Bot(agents.User):
    """A very basic autonomous agent"""

    is_alive = False

    def __init__(self, app, name=None):
        name = name if name else choice(lists.names)
        emoji = choice(lists.emojis)
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

    def perform(self):
        """Ignore requests to perform. To be implemented in subclasses."""
        pass


class NoTokenException(KeyError):
    pass


class AmbiguousTokenException(KeyError):
    pass


def bot_routine(bot):
    bot.start()
    bot.perform()
    bot.stop()


def create_bot(current_app, name=None):
    bot = Bot(current_app._get_current_object(), name)
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
