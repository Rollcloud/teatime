from random import choice

from flask import current_app

from .. import socketio
from . import agents
from . import behaviours
from . import bots
from . import lists

behaviour_flag = {
    'e': behaviours.Ehco,
    'f': behaviours.Follow,
    'p': behaviours.Puppy,
    'q': behaviours.Quote,
    'r': behaviours.Rollcall,
    's': behaviours.Silent,
}


class NoTokenException(KeyError):
    pass


class AmbiguousTokenException(KeyError):
    pass


def bot_routine(bot):
    bot.start()
    bot.perform()
    bot.stop()


def setup_bot(bot):
    agents.add_user(bot)
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


def new_user_joined(user):
    print(f"⭐ - {user} connected")

    # forward new user message to all other connected clients
    user.emit(
        'user_joined', {'user': user.asdict()}, broadcast=True, include_self=False
    )

    agents.add_user(user)

    # send own token to this connector
    user.emit('identify', {'token': user.token})
    # send all currently connected users to this connector
    for u in agents.get_users():
        user.emit('user_joined', {'user': u.asdict()})


def handle_text(user, message, recipients=None):
    if recipients:
        # forward message to all recipients
        user.emit(
            'message',
            {'handle': user.handle, 'msg': message, 'token': user.token},
            rooms=recipients,
        )
    else:
        # forward message to all connected clients
        user.emit(
            'message',
            {'handle': user.handle, 'msg': message, 'token': user.token},
            broadcast=True,
        )

    # special commands - only available to humans
    if type(user) == agents.User:

        # create bot
        if message.startswith("bot+"):
            app = current_app._get_current_object()
            bot = None

            # specify bot type after plus, eg: bot+q
            bot_type = message.split('+')[1]
            try:
                if bot_type == '':  # if no bot type provided after +, eg: bot+
                    bot = bots.CleverBot(
                        app, behaviour=choice(list(behaviour_flag.values()))
                    )
                elif bot_type == 'p':
                    bot = bots.CleverBot(
                        app, name="Spot", emoji="🐕", behaviour=behaviour_flag[bot_type],
                    )
                else:
                    bot = bots.CleverBot(app, behaviour=behaviour_flag[bot_type])
            except KeyError:  # Bot type not in behaviour_flag list
                user.emit(
                    'status', {'msg': f"bot_type '{bot_type}' not in behaviours list"},
                )

            if bot:
                user.emit(
                    'status',
                    {'msg': f"{user.handle} created bot {bot}"},
                    broadcast=True,
                )
                setup_bot(bot)

        # create alphabots
        if message == "bot++":
            for name in lists.names:
                bot = bots.CleverBot(app, name=name, behaviour=behaviours.Rollcall)
                user.emit(
                    'status',
                    {'msg': f"{user.handle} created bot {bot}"},
                    broadcast=True,
                )
                setup_bot(bot)

        # kill bot
        elif message.startswith("bot-"):
            token_hint = message.split('bot-')[1]
            try:
                bot = destroy_bot(token_hint)
                user.emit(
                    'status',
                    {'msg': f"{user.handle} killed bot {bot.token}"},
                    broadcast=True,
                )
            except KeyError as err:
                print(f"💥 Warning: {err}")


def handle_move(user, delta):
    user.pos_y += delta['y']
    user.pos_x += delta['x']

    response = {'token': user.token, 'pos_x': user.pos_x, 'pos_y': user.pos_y}

    # forward message to all connected clients
    user.emit('move', response, broadcast=True, include_self=False)


def user_left(user):
    print(f"💢 - {user} disconnecting")

    agents.remove_user(user.token)

    # forward message to all connected clients
    user.emit('user_left', {'user': user.asdict()}, broadcast=True)
