from flask import current_app, g
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Model = declarative_base()

def create_db_session():
    # Get the db address from the current app
    _db_address = current_app.config['SQLALCHEMY_DATABASE_URI']

    engine = create_engine(_db_address, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    Model.query = db_session.query_property()
    return db_session

def init_db():
    engine = g.db_session.get_bind()
    from orvsd_central import models
    Model.metadata.create_all(bind=engine)
