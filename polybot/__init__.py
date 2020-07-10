from datetime import datetime
import platform
import os

from flask import Flask, render_template

from polybot.version import __version__  # noqa: F401


def create_app(test_config: dict = None) -> Flask:
    """Create the polybot server application"""

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # Load in the configuration
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile(os.path.join(os.path.dirname(__file__), 'config.py'), silent=True)
        print(app.config)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # Make the initial status page
    start_time = datetime.now().isoformat()

    @app.route('/')
    def home():
        return render_template('home.html',
                               message=f'Running on {platform.node()} since {start_time}')

    # Load the blueprints
    from .views import ingest
    app.register_blueprint(ingest.bp)

    return app
