from django.urls import path
from . import views

urlpatterns = [
    path('about/',            views.about_view,          name='about'),
    path('about/edit/',       views.about_edit_view,     name='about_edit'),
    path('resume/download/',  views.resume_download_view, name='resume_download'),
    path('resume/upload/',    views.resume_upload_view,   name='resume_upload'),
]
