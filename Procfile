release: python manage.py migrate
web: gunicorn medishop_proj.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
