from flask.ext.script import Manager

from orvsd_central import app

manager = Manager(app)

if __name__ == '__main__':
    manager.run()
