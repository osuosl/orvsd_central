import os
_basedir = os.path.abspath(os.path.dirname(__file__))

#use 'dev', 'test', or 'production'
DATABASE_TYPE = 'test'



DEBUG = False

SECRET_KEY = "ay98r0u2q9305jr2or@QTG%#QH^KWTRTGrqy43"

if DATABASE_TYPE == 'test' or DATABASE_TYPE == 'dev':
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'db/orvsd_%s.db' % DATABASE_TYPE)
elif DATABASE_TYPE == 'production':
    #Add mysql URI
    SQLALCHEMY_DATABASE_URI = 'mysql://user:password@server/db'
else:
    raise NameError('The value used for DATABASE_TYPE is not an accepted value.')
DATABASE_CONNECT_OPTIONS = {}

CSRF_ENABLED = True
CSRF_SESSION_KEY="aser43wAG$#WAg43WAY$JH%j%$KJW%$uWA$5eYaEgsahsu"

SQLALCHEMY_MIGRATE_REPO = os.path.join(_basedir, '/db')
