from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.members.models import Appointment
from .models import NoShowPrediction
from .serializers import NoShowPredictionSerializer
from .ml_model import predict_no_show


@api_view(["POST"])
def predict_appointment_no_show(request, appointment_id):
    """
    Run the ML model on a specific appointment and store the prediction.
    # TODO: integrate with actual scheduling API to auto-predict on new bookings
    """
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    member = appointment.member

    result = predict_no_show(member, appointment)

    prediction = NoShowPrediction.objects.create(
        member=member,
        appointment=appointment,
        probability=result["probability"],
        risk_level=result["risk_level"],
        features_used=result["features"],
    )

    member.risk_score = result["probability"]
    member.save(update_fields=["risk_score"])

    serializer = NoShowPredictionSerializer(prediction)
    return Response(
        {
            **serializer.data,
            "top_risk_factors": result["top_risk_factors"],
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def high_risk_appointments(request):
    """
    List all upcoming appointments that have been flagged as high risk.
    If an appointment hasn't been scored yet, we score it on the fly.

    At Lantern this was the primary view coordinators used every morning
    to decide who to call first.
    """
    now = timezone.now()
    upcoming = Appointment.objects.filter(
        status="scheduled",
        appointment_date__gte=now,
    ).select_related("member")

    high_risk = []

    for appointment in upcoming:
        latest_prediction = appointment.predictions.first()

        if latest_prediction and latest_prediction.risk_level == "high":
            high_risk.append(latest_prediction)
        elif not latest_prediction:
            result = predict_no_show(appointment.member, appointment)
            if result["risk_level"] == "high":
                prediction = NoShowPrediction.objects.create(
                    member=appointment.member,
                    appointment=appointment,
                    probability=result["probability"],
                    risk_level=result["risk_level"],
                    features_used=result["features"],
                )
                high_risk.append(prediction)

    serializer = NoShowPredictionSerializer(high_risk, many=True)
    return Response(
        {
            "count": len(high_risk),
            "results": serializer.data,
        }
    )
