from django.db import migrations, models
class Migration(migrations.Migration):
    initial=True
    dependencies=[]
    operations=[
        migrations.CreateModel(name='ContactMessage',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False)),('name',models.CharField(max_length=120)),('email',models.EmailField()),('phone',models.CharField(blank=True,max_length=20)),('subject',models.CharField(max_length=200)),('message',models.TextField()),('created_at',models.DateTimeField(auto_now_add=True)),('is_read',models.BooleanField(default=False))],options={'ordering':['-created_at']}),
        migrations.CreateModel(name='ResumeFile',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False)),('file',models.FileField(upload_to='resume/')),('filename',models.CharField(max_length=255)),('uploaded_at',models.DateTimeField(auto_now=True)),('is_active',models.BooleanField(default=True))],options={'ordering':['-uploaded_at']}),
    ]
