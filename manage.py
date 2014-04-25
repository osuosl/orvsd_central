from flask import current_app, g
from flask.ext.script import Manager

from orvsd_central import attach_blueprints, create_app
from orvsd_central.database import create_db_session, init_db

def setup_app(config=None):
    app = create_app(config) if config else create_app()
    with app.app_context():
        g.db_session = create_db_session()
        attach_blueprints()
        return app

manager = Manager(setup_app)
manager.add_option('-c', '--config', dest='config')

@manager.command
def gather():
    with current_app.app_context():
        from orvsd_central.util import gather_siteinfo
        g.db_session = create_db_session()
        gather_siteinfo()

@manager.command
def initdb():
    with current_app.app_context():
        g.db_session = create_db_session()
        init_db()

if __name__ == '__main__':
    manager.run()
