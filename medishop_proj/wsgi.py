import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medishop_proj.settings')
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()