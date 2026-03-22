from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_view, name='health'),
    path('api/health/predict/', views.api_health_predict, name='api_health_predict'),
]
