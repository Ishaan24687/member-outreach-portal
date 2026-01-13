from django.db import models
from apps.members.models import Member, Appointment


class NoShowPrediction(models.Model):
    RISK_LEVEL_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="predictions"
    )
    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name="predictions"
    )
    probability = models.FloatField(
        help_text="Predicted probability of no-show (0.0 to 1.0)"
    )
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES)
    features_used = models.JSONField(
        default=dict,
        help_text="Feature values that went into this prediction",
    )
    predicted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-predicted_at"]
        get_latest_by = "predicted_at"

    def __str__(self):
        return (
            f"Prediction for {self.member.full_name}: "
            f"{self.probability:.2%} ({self.risk_level})"
        )
