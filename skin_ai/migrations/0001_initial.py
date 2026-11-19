from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
class Migration(migrations.Migration):
    initial=True
    dependencies=[migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[migrations.CreateModel(name='SkinAnalysis',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False)),('condition',models.CharField(max_length=100)),('confidence',models.FloatField()),('model_used',models.CharField(default='google/vit-base-patch16-224',max_length=100)),('created_at',models.DateTimeField(auto_now_add=True)),('user',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='skin_analyses',to=settings.AUTH_USER_MODEL))])]
