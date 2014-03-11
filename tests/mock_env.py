import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import orvsd_central
from orvsd_central import models
from orvsd_central.database import Model


class TestBase(unittest.TestCase):

    def setUp(self):
        """
        Create a test database in memory
        """
        self.test_engine = create_engine("sqlite:///:memory:",
                                         convert_unicode=True)
        self.db_session = scoped_session(sessionmaker(autocommit=True,
                                                      autoflush=True,
                                                      bind=self.test_engine))
        Model.query = self.db_session.query_property()

        # Create the tables
        Model.metadata.create_all(bind=self.test_engine)

        # Create the app
        self.app = orvsd_central.app.test_client()
        self.app.testing = True

    def tearDown(self):
        # Close the session and clean the db. Some tests may create
        # data and we don't want to keep that around
        self.db_session.remove()
        Model.metadata.drop_all(bind=self.test_engine)
