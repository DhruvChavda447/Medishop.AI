from django.contrib import admin
from .models import Appointment
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display=['patient_name','dr_name','dept','appt_date','status']
    list_filter=['status','dept']
