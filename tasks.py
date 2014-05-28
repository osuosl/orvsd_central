from celery import Celery
from flask import current_app

from manage import setup_app

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

celery_app = setup_app()
with celery_app.app_context():
    celery = init_celery(current_app)

if __name__ == "__main__":
    celery.start()
