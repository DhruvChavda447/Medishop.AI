from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
class Migration(migrations.Migration):
    initial=True
    dependencies=[migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[migrations.CreateModel(name='SentimentLog',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False)),('input_text',models.TextField()),('sentiment',models.CharField(max_length=20)),('confidence',models.FloatField()),('language',models.CharField(default='EN',max_length=10)),('response_generated',models.TextField(blank=True)),('created_at',models.DateTimeField(auto_now_add=True)),('user',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.CASCADE,related_name='sentiment_logs',to=settings.AUTH_USER_MODEL))],options={'ordering':['-created_at']})]
