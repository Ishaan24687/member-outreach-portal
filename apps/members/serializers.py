from rest_framework import serializers
from .models import Member, Appointment, OutreachEvent


class OutreachEventSerializer(serializers.ModelSerializer):
    outreach_type_display = serializers.CharField(
        source="get_outreach_type_display", read_only=True
    )
    outcome_display = serializers.CharField(
        source="get_outcome_display", read_only=True
    )

    class Meta:
        model = OutreachEvent
        fields = [
            "id",
            "member",
            "appointment",
            "outreach_type",
            "outreach_type_display",
            "outreach_date",
            "outcome",
            "outcome_display",
            "notes",
            "coordinator_name",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AppointmentSerializer(serializers.ModelSerializer):
    appointment_type_display = serializers.CharField(
        source="get_appointment_type_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    member_name = serializers.CharField(source="member.full_name", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "member",
            "member_name",
            "appointment_date",
            "appointment_type",
            "appointment_type_display",
            "provider_name",
            "location",
            "status",
            "status_display",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MemberSerializer(serializers.ModelSerializer):
    recent_appointments = serializers.SerializerMethodField()
    no_show_rate = serializers.FloatField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Member
        fields = [
            "id",
            "member_id",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "gender",
            "phone",
            "email",
            "zip_code",
            "insurance_plan",
            "risk_score",
            "no_show_rate",
            "recent_appointments",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "risk_score"]

    def get_recent_appointments(self, obj):
        recent = obj.appointments.all()[:5]
        return AppointmentSerializer(recent, many=True).data


class MemberListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views — skip nested appointments."""

    no_show_rate = serializers.FloatField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Member
        fields = [
            "id",
            "member_id",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "gender",
            "insurance_plan",
            "risk_score",
            "no_show_rate",
        ]
