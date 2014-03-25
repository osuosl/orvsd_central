from flask import current_app, g
from flask.ext.script import Manager

from orvsd_central import attach_blueprints, create_app
from orvsd_central.database import create_db_session, init_db

def setup_app(config):
    app = create_app(config) if config else create_app()
    with app.app_context():
        g.db_session = create_db_session()
        attach_blueprints()
        return app

manager = Manager(setup_app)
manager.add_option('-c', '--config', dest='config')

@manager.option('-d', '--dbconf', dest='conf')
def initdb(conf):
    app = create_app(conf)
    with app.app_context():
        g.db_session = create_db_session()
        init_db()

if __name__ == '__main__':
    manager.run()
