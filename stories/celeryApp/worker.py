from stories.app import start # pragma: no cover
from stories import celeryApp # pragma: no cover
'''
This script is used in order to creare a celery worker from command line
'''
app = start() # pragma: no cover
celery = celeryApp.make_celery(app) # pragma: no cover
celeryApp.celery = celery # pragma: no cover
