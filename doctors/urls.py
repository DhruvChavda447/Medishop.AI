from django.urls import path
from . import views

urlpatterns = [
    path('doctors/', views.doctors_view, name='doctors'),
    path('doctors/<int:did>/', views.doctor_detail_view, name='doctor_detail'),
    path('doctors/<int:did>/book/', views.book_appointment_view, name='book_appointment'),
    path('doctors/bill/<int:appt_id>/', views.checkup_bill_view, name='checkup_bill'),
    path('doctors/bill/<int:appt_id>/image/', views.checkup_bill_image_view, name='checkup_bill_image'),
    path('doctors/bill/<int:appt_id>/download/', views.checkup_bill_txt_view, name='checkup_bill_txt'),
    path('api/appointments/', views.api_appointments, name='api_appointments'),
    path('api/rag/chat/', views.api_rag_chat, name='api_rag_chat'),
    path('api/rag/upload-bill/', views.api_rag_upload_bill, name='api_rag_upload_bill'),
    path('api/rag/activate-bill/<int:appt_id>/', views.api_rag_activate_bill, name='api_rag_activate_bill'),
]
