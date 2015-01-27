import unittest

from contextlib import contextmanager
from flask import appcontext_pushed, g
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import orvsd_central
from orvsd_central import attach_blueprints
from orvsd_central.database import create_db_session
from orvsd_central.models import Model


class TestBase(unittest.TestCase):

    @contextmanager
    def database_set(self, app):
        def handler(sender, **kwargs):
            g.db_session = create_db_session()
        with appcontext_pushed.connected_to(handler, app):
            yield
            Model.metadata.drop_all(bind=g.db_session.get_bind())

    def setUp(self):
        """
        Create a test database in memory and a test app to be referenced as
        self.db_session and self.app respectively.
        """

        # Config modifications for testing
        db = 'sqlite:///:memory:'
        cfg = {
            'SQLALCHEMY_DATABASE_URI': db,
            'CELERY_BROKER_URL': 'sqla+' + db,
            'CELERY_RESULT_DBURI': db,
            'TESTING': True,
            'DEBUG': True
        }

        # Create the app
        self.app = orvsd_central.create_app(config_changes=cfg)
        self.app.testing = True

        with self.app.app_context():
            attach_blueprints()

            self.test_engine = create_engine(
                "sqlite:///:memory:",
                convert_unicode=True
            )
            g.db_session = scoped_session(
                sessionmaker(
                    autocommit=True,
                    autoflush=True,
                    bind=self.test_engine
                )
            )
            Model.query = g.db_session.query_property()

            # Create the tables
            Model.metadata.create_all(bind=self.test_engine)

    def tearDown(self):
        """
        Close the session and clean the db. Some tests may create
        data and we don't want to keep that around
        """
        Model.metadata.drop_all(bind=self.test_engine)
