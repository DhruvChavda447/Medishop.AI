from django.db import models
from django.contrib.auth.models import User


class Appointment(models.Model):
    STS = [('Confirmed', 'Confirmed'), ('Cancelled', 'Cancelled'), ('Completed', 'Completed')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    dr_id = models.IntegerField()
    dr_name = models.CharField(max_length=100)
    dept = models.CharField(max_length=80)
    appt_date = models.DateField()
    time_slot = models.CharField(max_length=20)
    reason = models.TextField(blank=True)
    patient_name = models.CharField(max_length=100)
    patient_phone = models.CharField(max_length=20, blank=True)
    fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STS, default='Confirmed')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient_name} — Dr. {self.dr_name} ({self.appt_date})"


class MedicalBill(models.Model):
    """Stores checkup bills generated after doctor appointment or uploaded by user for RAG chat."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_bills', null=True, blank=True)
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='bill', null=True, blank=True)
    bill_no = models.CharField(max_length=60, db_index=True)
    doctor_name = models.CharField(max_length=120, default='Consultar Physician')
    department = models.CharField(max_length=80, default='General Medicine')
    patient_name = models.CharField(max_length=120, default='Patient')
    bill_date = models.CharField(max_length=40, default='')
    diagnosis = models.TextField(blank=True)
    raw_text = models.TextField(blank=True)
    structured_json = models.TextField(default='{}')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    source_type = models.CharField(max_length=30, default='doctor_checkup')  # 'doctor_checkup' or 'uploaded_bill'
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.bill_no} — {self.patient_name} (₹{self.total_amount})"
