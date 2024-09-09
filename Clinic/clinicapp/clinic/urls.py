from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'users', views.MyUserViewSet, basename='users')
router.register(r'doctors', views.DoctorViewSet, basename='doctors')
router.register(r'appointments', views.AppointmentViewSet, basename='appointments')
router.register(r'medicines', views.MedicineViewSet, basename='medicines')
router.register(r'prescriptions', views.PrescriptionViewSet, basename='prescriptions')
router.register(r'invoices', views.InvoiceViewSet, basename='invoices')

urlpatterns = [
    path('', include(router.urls)),
    # path('report/', views.report_view, name='report_view'),
]