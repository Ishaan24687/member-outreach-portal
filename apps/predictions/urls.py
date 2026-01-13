from django.urls import path
from . import views

urlpatterns = [
    path(
        "predict/<int:appointment_id>/",
        views.predict_appointment_no_show,
        name="predict-no-show",
    ),
    path(
        "high-risk/",
        views.high_risk_appointments,
        name="high-risk-appointments",
    ),
]
