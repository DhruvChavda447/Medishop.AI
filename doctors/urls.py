from django.urls import path
from . import views
urlpatterns = [
    path('doctors/',               views.doctors_view,          name='doctors'),
    path('doctors/<int:did>/',     views.doctor_detail_view,    name='doctor_detail'),
    path('doctors/<int:did>/book/',views.book_appointment_view, name='book_appointment'),
    path('api/appointments/',      views.api_appointments,      name='api_appointments'),
]
