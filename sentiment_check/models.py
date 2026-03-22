from django.db import models
from django.contrib.auth.models import User
class SentimentLog(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    input_text=models.TextField(); sentiment=models.CharField(max_length=20)
    confidence=models.FloatField(); language=models.CharField(max_length=10,default='EN')
    response_generated=models.TextField(blank=True); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']
