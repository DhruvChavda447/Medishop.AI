"""Run this once to see migration structure — actual migrations created via manage.py"""
MIGRATION_TEMPLATE = '''from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = {deps}
    operations = {ops}
'''
