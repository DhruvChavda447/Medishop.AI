from django.urls import path
from . import views
urlpatterns = [
    path('skin/', views.skin_view, name='skin'),
    path('api/skin/analyze/', views.api_skin_analyze, name='api_skin_analyze'),
]
