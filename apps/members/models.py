from django.db import models


class Member(models.Model):
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    ]

    member_id = models.CharField(max_length=20, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    zip_code = models.CharField(max_length=10)
    insurance_plan = models.CharField(max_length=100)
    risk_score = models.FloatField(
        default=0.0,
        help_text="ML-generated risk score for no-show likelihood (0-1)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.member_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def no_show_rate(self):
        total = self.appointments.filter(
            status__in=["completed", "no_show"]
        ).count()
        if total == 0:
            return 0.0
        no_shows = self.appointments.filter(status="no_show").count()
        return round(no_shows / total, 3)


class Appointment(models.Model):
    TYPE_CHOICES = [
        ("surgery_consult", "Surgery Consultation"),
        ("follow_up", "Follow-Up"),
        ("pre_op", "Pre-Op Assessment"),
        ("post_op", "Post-Op Check"),
        ("physical_therapy", "Physical Therapy"),
    ]
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("completed", "Completed"),
        ("no_show", "No Show"),
        ("cancelled", "Cancelled"),
    ]

    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="appointments"
    )
    appointment_date = models.DateTimeField(db_index=True)
    appointment_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    provider_name = models.CharField(max_length=150)
    location = models.CharField(max_length=200)
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default="scheduled"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-appointment_date"]

    def __str__(self):
        return (
            f"{self.member.full_name} — "
            f"{self.get_appointment_type_display()} on "
            f"{self.appointment_date:%Y-%m-%d}"
        )


class OutreachEvent(models.Model):
    """
    Tracks every outreach attempt a coordinator makes.
    # at Lantern we saw that just calling patients 48 hours before
    # their appointment cut no-shows by 28%
    """

    OUTREACH_TYPE_CHOICES = [
        ("phone_call", "Phone Call"),
        ("sms", "SMS"),
        ("email", "Email"),
    ]
    OUTCOME_CHOICES = [
        ("reached", "Reached"),
        ("voicemail", "Voicemail"),
        ("no_answer", "No Answer"),
        ("wrong_number", "Wrong Number"),
    ]

    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="outreach_events"
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="outreach_events",
        null=True,
        blank=True,
    )
    outreach_type = models.CharField(max_length=15, choices=OUTREACH_TYPE_CHOICES)
    outreach_date = models.DateTimeField()
    outcome = models.CharField(max_length=15, choices=OUTCOME_CHOICES)
    notes = models.TextField(blank=True)
    coordinator_name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-outreach_date"]

    def __str__(self):
        return (
            f"{self.get_outreach_type_display()} to {self.member.full_name} "
            f"({self.get_outcome_display()})"
        )
