from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('doctors', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MedicalBill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bill_no', models.CharField(db_index=True, max_length=60)),
                ('doctor_name', models.CharField(default='Consultar Physician', max_length=120)),
                ('department', models.CharField(default='General Medicine', max_length=80)),
                ('patient_name', models.CharField(default='Patient', max_length=120)),
                ('bill_date', models.CharField(default='', max_length=40)),
                ('diagnosis', models.TextField(blank=True)),
                ('raw_text', models.TextField(blank=True)),
                ('structured_json', models.TextField(default='{}')),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('source_type', models.CharField(default='doctor_checkup', max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('appointment', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bill', to='doctors.appointment')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='medical_bills', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
