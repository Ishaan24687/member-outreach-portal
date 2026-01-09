from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"members", views.MemberViewSet, basename="member")
router.register(r"appointments", views.AppointmentViewSet, basename="appointment")
router.register(r"outreach", views.OutreachEventViewSet, basename="outreach")

urlpatterns = [
    path("", include(router.urls)),
]
