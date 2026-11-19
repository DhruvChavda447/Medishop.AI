release: python manage.py migrate --noinput
web: python manage.py migrate --noinput && gunicorn medishop_proj.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
