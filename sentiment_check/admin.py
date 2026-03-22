from django.contrib import admin
from .models import SentimentLog
@admin.register(SentimentLog)
class SentimentAdmin(admin.ModelAdmin):
    list_display=['sentiment','language','confidence','created_at']
    list_filter=['sentiment','language']
