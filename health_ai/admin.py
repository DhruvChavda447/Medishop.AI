from django.contrib import admin
from .models import HealthRiskLog

@admin.register(HealthRiskLog)
class HealthRiskLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'age', 'bmi', 'risk_label', 'risk_score', 'created_at']
    list_filter = ['risk_label', 'smoker', 'diabetes']
    ordering = ['-created_at']
