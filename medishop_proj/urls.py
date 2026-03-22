from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home_app.urls')),
    path('', include('core_auth.urls')),
    path('', include('shop.urls')),
    path('', include('doctors.urls')),
    path('', include('skin_ai.urls')),
    path('', include('sentiment_check.urls')),
    path('', include('portfolio.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
