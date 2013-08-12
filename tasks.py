from celery import Celery
from orvsd_central import app
import requests

def init_celery(app):
    celery = Celery("tasks", broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = init_celery(app)

if __name__ == "__main__":
    celery.start()
