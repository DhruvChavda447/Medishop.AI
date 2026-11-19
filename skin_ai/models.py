from django.db import models
from django.contrib.auth.models import User
class SkinAnalysis(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='skin_analyses')
    condition=models.CharField(max_length=100); confidence=models.FloatField()
    model_used=models.CharField(max_length=100,default='google/vit-base-patch16-224')
    created_at=models.DateTimeField(auto_now_add=True)
