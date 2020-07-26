from flask import Flask, current_app
from flask_socketio import SocketIO

socketio = SocketIO()


def create_app(debug=False):
    """Create an application."""
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'j&_^AJ*P5!V?5xjSCzU9'
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = True

    with app.app_context():
        current_app.users = {}

    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    socketio.init_app(app)

    return app
