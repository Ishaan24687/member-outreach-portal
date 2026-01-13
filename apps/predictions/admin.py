from django.contrib import admin
from .models import NoShowPrediction


@admin.register(NoShowPrediction)
class NoShowPredictionAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "appointment",
        "probability",
        "risk_level",
        "predicted_at",
    ]
    list_filter = ["risk_level"]
    readonly_fields = ["predicted_at", "features_used"]
