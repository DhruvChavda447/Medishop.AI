#!/bin/bash
echo "🚀 Setting up MediShop Pro..."
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
echo ""
echo "✅ Setup complete!"
echo "Run: python manage.py runserver"
echo "Then go to: http://127.0.0.1:8000/signup/"
