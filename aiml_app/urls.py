from django.urls import path
from . import views

urlpatterns = [
    path('aiml/', views.aiml_view, name='aiml'),
]
