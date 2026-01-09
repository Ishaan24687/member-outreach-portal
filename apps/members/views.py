from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Member, Appointment, OutreachEvent
from .serializers import (
    MemberSerializer,
    MemberListSerializer,
    AppointmentSerializer,
    OutreachEventSerializer,
)


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["first_name", "last_name", "member_id", "zip_code"]
    ordering_fields = ["last_name", "risk_score", "created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return MemberListSerializer
        return MemberSerializer

    @action(detail=True, methods=["get"], url_path="risk_score")
    def get_risk_score(self, request, pk=None):
        """
        Call the ML model to get a fresh no-show risk score for this member.
        Uses their most recent upcoming appointment if available.
        """
        member = self.get_object()
        upcoming = member.appointments.filter(status="scheduled").first()

        if not upcoming:
            return Response(
                {"detail": "No upcoming scheduled appointments for this member."},
                status=status.HTTP_404_NOT_FOUND,
            )

        from apps.predictions.ml_model import predict_no_show

        prediction = predict_no_show(member, upcoming)

        member.risk_score = prediction["probability"]
        member.save(update_fields=["risk_score"])

        return Response(
            {
                "member_id": member.member_id,
                "member_name": member.full_name,
                "appointment_id": upcoming.id,
                "appointment_date": upcoming.appointment_date,
                "probability": prediction["probability"],
                "risk_level": prediction["risk_level"],
                "top_risk_factors": prediction["top_risk_factors"],
            }
        )


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related("member").all()
    serializer_class = AppointmentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["member__first_name", "member__last_name", "provider_name"]
    ordering_fields = ["appointment_date", "status"]

    def get_queryset(self):
        qs = super().get_queryset()
        appt_status = self.request.query_params.get("status")
        if appt_status:
            qs = qs.filter(status=appt_status)
        member_id = self.request.query_params.get("member")
        if member_id:
            qs = qs.filter(member_id=member_id)
        return qs

    @action(detail=True, methods=["patch"], url_path="update-status")
    def update_status(self, request, pk=None):
        appointment = self.get_object()
        new_status = request.data.get("status")
        if new_status not in dict(Appointment.STATUS_CHOICES):
            return Response(
                {"detail": f"Invalid status. Choose from: {[c[0] for c in Appointment.STATUS_CHOICES]}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        appointment.status = new_status
        appointment.save(update_fields=["status"])
        return Response(AppointmentSerializer(appointment).data)


class OutreachEventViewSet(viewsets.ModelViewSet):
    queryset = OutreachEvent.objects.select_related("member", "appointment").all()
    serializer_class = OutreachEventSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["coordinator_name", "member__first_name", "member__last_name"]
    ordering_fields = ["outreach_date", "outcome"]

    def get_queryset(self):
        qs = super().get_queryset()
        coordinator = self.request.query_params.get("coordinator")
        if coordinator:
            qs = qs.filter(coordinator_name__icontains=coordinator)
        member_id = self.request.query_params.get("member")
        if member_id:
            qs = qs.filter(member_id=member_id)
        return qs


# Template views

def member_list_view(request):
    members = Member.objects.all()
    search = request.GET.get("search", "")
    if search:
        members = members.filter(
            models.Q(first_name__icontains=search)
            | models.Q(last_name__icontains=search)
            | models.Q(member_id__icontains=search)
        )
    return render(request, "member_list.html", {"members": members, "search": search})


def member_detail_view(request, pk):
    member = get_object_or_404(Member, pk=pk)
    appointments = member.appointments.all()
    outreach = member.outreach_events.all()
    return render(
        request,
        "member_detail.html",
        {"member": member, "appointments": appointments, "outreach_events": outreach},
    )
