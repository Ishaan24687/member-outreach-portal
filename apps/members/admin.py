from django.contrib import admin
from .models import Member, Appointment, OutreachEvent


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = [
        "member_id",
        "first_name",
        "last_name",
        "date_of_birth",
        "insurance_plan",
        "risk_score",
        "created_at",
    ]
    list_filter = ["gender", "insurance_plan"]
    search_fields = ["first_name", "last_name", "member_id", "email"]
    readonly_fields = ["created_at"]


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "appointment_date",
        "appointment_type",
        "provider_name",
        "status",
    ]
    list_filter = ["status", "appointment_type"]
    search_fields = ["member__first_name", "member__last_name", "provider_name"]
    readonly_fields = ["created_at"]
    date_hierarchy = "appointment_date"


@admin.register(OutreachEvent)
class OutreachEventAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "outreach_type",
        "outreach_date",
        "outcome",
        "coordinator_name",
    ]
    list_filter = ["outreach_type", "outcome", "coordinator_name"]
    search_fields = ["member__first_name", "member__last_name", "coordinator_name"]
    readonly_fields = ["created_at"]
    date_hierarchy = "outreach_date"
