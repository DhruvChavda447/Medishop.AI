from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.models import User
# After deploy, visit /create-admin/ once to create superuser
from django.http import HttpResponse
def create_admin(request):
    if not User.objects.filter(username='dhruv').exists():
        User.objects.create_superuser('dhruv','dhruvchavda.intern@gmail.com','Admin@1234')
        return HttpResponse('Admin created! username: dhruv password: Admin@1234')
    return HttpResponse('Already exists')

def run_migrate(request):
    from django.core.management import call_command
    import io
    out = io.StringIO()
    call_command('migrate', stdout=out)
    return HttpResponse(out.getvalue().replace('\n','<br>'))
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home_app.urls')),
    path('', include('core_auth.urls')),
    path('', include('shop.urls')),
    path('', include('doctors.urls')),
    path('', include('skin_ai.urls')),
    path('', include('sentiment_check.urls')),
    path('', include('portfolio.urls')),
path('run-migrate/', run_migrate),

path('create-admin/', create_admin),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
