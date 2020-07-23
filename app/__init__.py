from flask import Flask, current_app
from flask_executor import Executor
from flask_socketio import SocketIO

executor = Executor()
socketio = SocketIO()


def create_app(debug=False):
    """Create an application."""
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'
    app.config['SESSION_PERMANENT'] = True
    app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = True

    app.config.update(SESSION_COOKIE_SAMESITE='Lax')

    with app.app_context():
        current_app.areas = {}

    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    executor.init_app(app)
    socketio.init_app(app)

    return app
