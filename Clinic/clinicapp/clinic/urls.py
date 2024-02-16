from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register('users', views.MyUserViewSet, basename='users')
router.register('appointments', views.AppointmentViewSet, basename='appointments')
# router.register('prescriptions', views.PrescriptionViewSet, basename='prescriptions')

urlpatterns = [
    path('', include(router.urls))
]