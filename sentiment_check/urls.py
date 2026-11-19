from django.urls import path
from . import views

urlpatterns = [
    path('sentiment/', views.sentiment_view, name='sentiment'),
    path('api/sentiment/', views.api_sentiment, name='api_sentiment'),
    path('api/sentiment/chat/', views.api_sentiment_chat, name='api_sentiment_chat'),
]
