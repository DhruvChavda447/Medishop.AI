from django.db import models
from django.contrib.auth.models import User

class Appointment(models.Model):
    STS = [('Confirmed','Confirmed'),('Cancelled','Cancelled'),('Completed','Completed')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    dr_id=models.IntegerField(); dr_name=models.CharField(max_length=100)
    dept=models.CharField(max_length=80); appt_date=models.DateField()
    time_slot=models.CharField(max_length=20); reason=models.TextField(blank=True)
    patient_name=models.CharField(max_length=100); patient_phone=models.CharField(max_length=20,blank=True)
    fee=models.DecimalField(max_digits=8,decimal_places=2,null=True,blank=True)
    status=models.CharField(max_length=20,choices=STS,default='Confirmed')
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']
    def __str__(self): return f"{self.patient_name} — Dr.{self.dr_name} {self.appt_date}"
