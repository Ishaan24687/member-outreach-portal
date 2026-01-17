"""
Analytics API endpoints.

These mirror the Streamlit dashboard I built at Lantern — coordinators
wanted to see at a glance whether their outreach was actually moving the
needle on no-show rates.
"""

from datetime import timedelta
from collections import defaultdict

from django.db.models import Count, Q, F
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.members.models import Member, Appointment, OutreachEvent


@api_view(["GET"])
def overview(request):
    """
    Dashboard KPIs: total members, appointments this month,
    current no-show rate, and outreach conversion rate.
    """
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_members = Member.objects.count()

    appointments_this_month = Appointment.objects.filter(
        appointment_date__gte=month_start,
        appointment_date__lte=now,
    ).count()

    completed_or_no_show = Appointment.objects.filter(
        appointment_date__gte=month_start,
        status__in=["completed", "no_show"],
    )
    total_resolved = completed_or_no_show.count()
    no_shows = completed_or_no_show.filter(status="no_show").count()
    no_show_rate = round(no_shows / total_resolved, 4) if total_resolved > 0 else 0.0

    # outreach conversion: member was reached AND then showed up
    outreach_this_month = OutreachEvent.objects.filter(
        outreach_date__gte=month_start
    )
    total_outreach = outreach_this_month.count()
    reached = outreach_this_month.filter(outcome="reached")
    reached_and_showed = 0
    for event in reached:
        if event.appointment and event.appointment.status == "completed":
            reached_and_showed += 1
    outreach_conversion = (
        round(reached_and_showed / total_outreach, 4) if total_outreach > 0 else 0.0
    )

    return Response(
        {
            "total_members": total_members,
            "appointments_this_month": appointments_this_month,
            "no_show_rate": no_show_rate,
            "outreach_conversion_rate": outreach_conversion,
            "period": {
                "start": month_start.isoformat(),
                "end": now.isoformat(),
            },
        }
    )


@api_view(["GET"])
def trends(request):
    """
    Weekly no-show rate over the last 12 weeks.
    This is the trend line chart coordinators check every Monday.
    """
    now = timezone.now()
    weeks = []

    for i in range(12, 0, -1):
        week_end = now - timedelta(weeks=i - 1)
        week_start = week_end - timedelta(weeks=1)

        resolved = Appointment.objects.filter(
            appointment_date__gte=week_start,
            appointment_date__lt=week_end,
            status__in=["completed", "no_show"],
        )
        total = resolved.count()
        no_shows = resolved.filter(status="no_show").count()

        weeks.append(
            {
                "week_start": week_start.date().isoformat(),
                "week_end": week_end.date().isoformat(),
                "total_appointments": total,
                "no_shows": no_shows,
                "no_show_rate": round(no_shows / total, 4) if total > 0 else 0.0,
            }
        )

    return Response({"weeks": weeks})


@api_view(["GET"])
def outreach_effectiveness(request):
    """
    Break down outreach by type: how many attempted, how many reached,
    and of those reached, how many then showed up for their appointment.

    # at Lantern we saw that just calling patients 48 hours before
    # their appointment cut no-shows by 28%
    """
    results = []

    for outreach_type, display in OutreachEvent.OUTREACH_TYPE_CHOICES:
        events = OutreachEvent.objects.filter(outreach_type=outreach_type)
        total = events.count()
        reached = events.filter(outcome="reached").count()

        showed_up = 0
        for event in events.filter(outcome="reached"):
            if event.appointment and event.appointment.status == "completed":
                showed_up += 1

        results.append(
            {
                "outreach_type": outreach_type,
                "display_name": display,
                "total_attempts": total,
                "reached": reached,
                "reach_rate": round(reached / total, 4) if total > 0 else 0.0,
                "showed_up_after_contact": showed_up,
                "conversion_rate": (
                    round(showed_up / reached, 4) if reached > 0 else 0.0
                ),
            }
        )

    return Response({"by_outreach_type": results})


@api_view(["GET"])
def coordinator_performance(request):
    """
    Per-coordinator metrics: outreach count, reach rate, and conversion.
    Supervisors used this at Lantern to identify top performers and
    figure out what they were doing differently.
    """
    coordinators = (
        OutreachEvent.objects.values("coordinator_name")
        .annotate(
            total_outreach=Count("id"),
            reached_count=Count("id", filter=Q(outcome="reached")),
        )
        .order_by("-total_outreach")
    )

    results = []
    for coord in coordinators:
        name = coord["coordinator_name"]
        total = coord["total_outreach"]
        reached = coord["reached_count"]

        reached_events = OutreachEvent.objects.filter(
            coordinator_name=name, outcome="reached"
        )
        showed_up = 0
        for event in reached_events:
            if event.appointment and event.appointment.status == "completed":
                showed_up += 1

        results.append(
            {
                "coordinator_name": name,
                "total_outreach": total,
                "reached": reached,
                "reach_rate": round(reached / total, 4) if total > 0 else 0.0,
                "showed_up_after_contact": showed_up,
                "success_rate": (
                    round(showed_up / reached, 4) if reached > 0 else 0.0
                ),
            }
        )

    return Response({"coordinators": results})
