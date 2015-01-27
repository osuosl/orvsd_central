from flask import Flask, current_app, g

from orvsd_central.database import create_db_session


def create_app(config='config.default', config_changes=None):
    """
    Creates an instance of our application.

    We needed to create the app in this way so we could set different
    configurations within the same app. (hint: not using the same database
    when testing)
    """

    app = Flask(__name__)
    app.config.from_object(config)

    if config_changes:
        app.config.update(config_changes)

    with app.app_context():
        g.db_session = create_db_session()
        attach_blueprints()
        return app


def attach_blueprints():
    from orvsd_central.controllers import api
    from orvsd_central.controllers import category
    from orvsd_central.controllers import general
    from orvsd_central.controllers import report

    current_app.register_blueprint(api.mod)
    current_app.register_blueprint(category.mod)
    current_app.register_blueprint(general.mod)
    current_app.register_blueprint(report.mod)
