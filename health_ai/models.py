from django.db import models
from django.contrib.auth.models import User

class HealthRiskLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health_risks', null=True, blank=True)
    age = models.IntegerField()
    bmi = models.FloatField()
    blood_pressure_systolic = models.IntegerField()
    blood_pressure_diastolic = models.IntegerField()
    glucose = models.FloatField()
    cholesterol = models.FloatField()
    heart_rate = models.IntegerField()
    smoker = models.BooleanField(default=False)
    diabetes = models.BooleanField(default=False)
    family_history = models.BooleanField(default=False)
    activity_level = models.CharField(max_length=20, default='moderate')
    risk_score = models.FloatField()
    risk_label = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.risk_label} ({self.risk_score:.1f}%)"
