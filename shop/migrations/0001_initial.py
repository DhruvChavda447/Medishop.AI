from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
class Migration(migrations.Migration):
    initial=True
    dependencies=[migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name='Cart',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False)),('items',models.JSONField(default=list)),('updated_at',models.DateTimeField(auto_now=True)),('user',models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name='cart',to=settings.AUTH_USER_MODEL))]),
        migrations.CreateModel(name='Order',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False)),('order_ref',models.CharField(max_length=30,unique=True)),('items',models.JSONField(default=list)),('total',models.DecimalField(decimal_places=2,max_digits=10)),('address',models.TextField()),('payment_method',models.CharField(choices=[('upi','UPI'),('card','Card'),('cod','Cash on Delivery')],max_length=10)),('status',models.CharField(choices=[('Confirmed','Confirmed'),('Processing','Processing'),('Shipped','Shipped'),('Delivered','Delivered'),('Cancelled','Cancelled')],default='Confirmed',max_length=20)),('created_at',models.DateTimeField(auto_now_add=True)),('user',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='orders',to=settings.AUTH_USER_MODEL))],options={'ordering':['-created_at']}),
    ]
