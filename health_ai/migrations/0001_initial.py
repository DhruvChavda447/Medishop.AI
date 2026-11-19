from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='HealthRiskLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('age', models.IntegerField()),
                ('bmi', models.FloatField()),
                ('blood_pressure_systolic', models.IntegerField()),
                ('blood_pressure_diastolic', models.IntegerField()),
                ('glucose', models.FloatField()),
                ('cholesterol', models.FloatField()),
                ('heart_rate', models.IntegerField()),
                ('smoker', models.BooleanField(default=False)),
                ('diabetes', models.BooleanField(default=False)),
                ('family_history', models.BooleanField(default=False)),
                ('activity_level', models.CharField(default='moderate', max_length=20)),
                ('risk_score', models.FloatField()),
                ('risk_label', models.CharField(max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='health_risks',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
