from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
class Migration(migrations.Migration):
    initial=True
    dependencies=[migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name='Appointment',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False)),('dr_id',models.IntegerField()),('dr_name',models.CharField(max_length=100)),('dept',models.CharField(max_length=80)),('appt_date',models.DateField()),('time_slot',models.CharField(max_length=20)),('reason',models.TextField(blank=True)),('patient_name',models.CharField(max_length=100)),('patient_phone',models.CharField(blank=True,max_length=20)),('fee',models.DecimalField(blank=True,decimal_places=2,max_digits=8,null=True)),('status',models.CharField(choices=[('Confirmed','Confirmed'),('Cancelled','Cancelled'),('Completed','Completed')],default='Confirmed',max_length=20)),('created_at',models.DateTimeField(auto_now_add=True)),('user',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='appointments',to=settings.AUTH_USER_MODEL))],options={'ordering':['-created_at']}),
    ]
