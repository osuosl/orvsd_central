from manage import setup_app

celery_app = setup_app()

with celery_app.app_context():
    from orvsd_central.util import init_celery

    celery = init_celery()
    celery.start()
