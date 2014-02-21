from flask.ext.script import Manager

from orvsd_central import app

manager = Manager(app)


@manager.command
def initdb():
    from orvsd_central.database import init_db
    init_db()


if __name__ == '__main__':
    manager.run()
