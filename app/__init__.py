from flask import Flask, current_app
from flask_socketio import SocketIO

socketio = SocketIO()


def create_app(debug=False):
    """Create an application."""
    app = Flask(__name__)
    app.debug = debug
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = True

    app.config.from_object('config_default')
    app.config.from_object('config')

    if not app.config['SECRET_KEY']:
        raise ValueError(
            "Please set constant SECRET_KEY in 'config.py' for Flask application"
        )

    with app.app_context():
        current_app.users = {}

    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    socketio.init_app(app)  # , logger=True, engineio_logger=True)

    return app
