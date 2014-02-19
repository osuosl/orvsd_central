from flask import current_app
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Get the db address from the current app
_db_address = current_app.config['SQLALCHEMY_DB_URI']

engine = create_engine(_db_address, convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Model = declarative_base()
Model.query = db_session.query_property()

def init_db():
    from orvsd_central import models
    Model.metadata.create_all(bind=engine)
