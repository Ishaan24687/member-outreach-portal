from rest_framework import serializers
from .models import NoShowPrediction


class NoShowPredictionSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)
    appointment_date = serializers.DateTimeField(
        source="appointment.appointment_date", read_only=True
    )
    appointment_type = serializers.CharField(
        source="appointment.get_appointment_type_display", read_only=True
    )

    class Meta:
        model = NoShowPrediction
        fields = [
            "id",
            "member",
            "member_name",
            "appointment",
            "appointment_date",
            "appointment_type",
            "probability",
            "risk_level",
            "features_used",
            "predicted_at",
        ]
        read_only_fields = ["id", "predicted_at"]
