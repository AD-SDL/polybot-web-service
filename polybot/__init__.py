from datetime import datetime
import platform

from flask import Flask, render_template


def create_app(test_config: dict = None) -> Flask:
    """Create the polybot server application"""

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # Load in the configuration
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # Make the initial status page
    start_time = datetime.now().isoformat()

    @app.route('/')
    def home():
        return render_template('home.html', message=f'Running on {platform.node()} since {start_time}')

    return app
