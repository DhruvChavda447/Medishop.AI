from django.contrib import admin
from .models import ContactMessage, ResumeFile, AboutProfile

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name','email','subject','created_at','is_read']
    list_filter = ['is_read']
    ordering = ['-created_at']
    actions = ['mark_read']
    def mark_read(self, request, qs): qs.update(is_read=True)
    mark_read.short_description = 'Mark as read'

@admin.register(ResumeFile)
class ResumeFileAdmin(admin.ModelAdmin):
    list_display = ['filename','uploaded_at','is_active']

@admin.register(AboutProfile)
class AboutProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name','email','company','updated_at']
