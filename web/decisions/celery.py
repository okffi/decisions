from __future__ import absolute_import
import os
import site

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decisions.settings')

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
site.addsitedir(os.path.join(PROJECT_DIR, "vendor"))

from django.conf import settings # noqa

app = Celery('decisions')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# --- Project-wide tasks ---

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
