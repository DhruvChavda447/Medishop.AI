from django.urls import path
from . import views
urlpatterns = [
    path('sentiment/', views.sentiment_view, name='sentiment'),
    path('api/sentiment/', views.api_sentiment, name='api_sentiment'),
]
