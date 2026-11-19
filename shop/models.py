from django.db import models
from django.contrib.auth.models import User

class Cart(models.Model):
    user  = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    items = models.JSONField(default=list)  # [{"id":1,"qty":2},...]
    updated_at = models.DateTimeField(auto_now=True)
    def total_qty(self): return sum(i.get('qty',0) for i in self.items)
    def __str__(self): return f"{self.user.username} Cart"

class Order(models.Model):
    PAY = [('upi','UPI'),('card','Card'),('cod','Cash on Delivery')]
    STS = [('Confirmed','Confirmed'),('Processing','Processing'),('Shipped','Shipped'),('Delivered','Delivered'),('Cancelled','Cancelled')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_ref = models.CharField(max_length=30, unique=True)
    items = models.JSONField(default=list)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.TextField()
    payment_method = models.CharField(max_length=10, choices=PAY)
    status = models.CharField(max_length=20, choices=STS, default='Confirmed')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']
    def __str__(self): return f"{self.order_ref} — {self.user.username}"
    def get_payment_method_display(self):
        return dict(self.PAY).get(self.payment_method, self.payment_method)
