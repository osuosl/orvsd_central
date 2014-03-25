from flask import Flask, current_app

def create_app(config='config.default'):
    app = Flask(__name__)
    app.config.from_object(config)
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
