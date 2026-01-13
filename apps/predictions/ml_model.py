"""
No-show prediction model interface.

Loads a trained GradientBoostingClassifier from disk and exposes
extract_features() and predict_no_show() for the rest of the app.

If the model file hasn't been trained yet, returns a heuristic-based
default risk so the app still works without the ML pipeline.
"""

import logging
from datetime import date, datetime

import joblib
import numpy as np
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

_model = None
_feature_names = None


def _load_model():
    global _model, _feature_names
    model_path = settings.ML_MODEL_PATH

    try:
        data = joblib.load(model_path)
        _model = data["model"]
        _feature_names = data["feature_names"]
        logger.info("Loaded no-show model from %s", model_path)
    except FileNotFoundError:
        logger.warning(
            "No trained model found at %s — using heuristic fallback. "
            "Run `python ml/train.py` to train the model.",
            model_path,
        )
        _model = None
    except Exception:
        logger.exception("Failed to load model from %s", model_path)
        _model = None


def _ensure_model_loaded():
    if _model is None and _feature_names is None:
        _load_model()


APPOINTMENT_TYPE_MAP = {
    "surgery_consult": 0,
    "follow_up": 1,
    "pre_op": 2,
    "post_op": 3,
    "physical_therapy": 4,
}


def extract_features(member, appointment):
    """
    Build the feature dict the model expects.

    Features are based on what we found predictive at Lantern:
    historical no-show rate was by far the strongest signal, followed
    by how far out the appointment was scheduled and whether the
    member had been contacted recently.
    """
    now = timezone.now()

    if isinstance(appointment.appointment_date, datetime):
        appt_dt = appointment.appointment_date
    else:
        appt_dt = timezone.make_aware(
            datetime.combine(appointment.appointment_date, datetime.min.time())
        )

    days_until = max((appt_dt - now).days, 0)

    past_appointments = member.appointments.filter(
        status__in=["completed", "no_show"]
    )
    total_past = past_appointments.count()
    no_shows = past_appointments.filter(status="no_show").count()
    historical_no_show_rate = no_shows / total_past if total_past > 0 else 0.0

    past_outreach_count = member.outreach_events.count()

    dob = member.date_of_birth
    if isinstance(dob, str):
        dob = date.fromisoformat(dob)
    member_age = (date.today() - dob).days / 365.25

    appt_type_encoded = APPOINTMENT_TYPE_MAP.get(appointment.appointment_type, 0)
    is_monday = appt_dt.weekday() == 0
    is_follow_up = appointment.appointment_type == "follow_up"

    # rough distance estimate from zip code prefix
    # TODO: integrate with actual geocoding API
    try:
        zip_num = int(member.zip_code[:3])
        distance_estimate = (zip_num % 50) + 1
    except (ValueError, TypeError):
        distance_estimate = 15

    return {
        "days_until_appointment": days_until,
        "historical_no_show_rate": round(historical_no_show_rate, 4),
        "appointment_type_encoded": appt_type_encoded,
        "member_age": round(member_age, 1),
        "total_past_appointments": total_past,
        "past_outreach_count": past_outreach_count,
        "distance_estimate": distance_estimate,
        "is_monday": int(is_monday),
        "is_follow_up": int(is_follow_up),
    }


def predict_no_show(member, appointment):
    """
    Predict the probability of a no-show for a given member + appointment.

    Returns a dict with probability, risk_level, and top_risk_factors.
    Falls back to a heuristic if no trained model is available.
    """
    _ensure_model_loaded()
    features = extract_features(member, appointment)

    if _model is not None:
        feature_vector = np.array(
            [[features[f] for f in _feature_names]]
        )
        probability = float(_model.predict_proba(feature_vector)[0][1])

        importances = _model.feature_importances_
        feature_importance_pairs = sorted(
            zip(_feature_names, importances), key=lambda x: x[1], reverse=True
        )
        top_risk_factors = [
            {"feature": name, "importance": round(float(imp), 4)}
            for name, imp in feature_importance_pairs[:5]
        ]
    else:
        # heuristic fallback when model file doesn't exist
        probability = _heuristic_risk(features)
        top_risk_factors = [
            {"feature": "historical_no_show_rate", "importance": 0.35},
            {"feature": "days_until_appointment", "importance": 0.20},
            {"feature": "past_outreach_count", "importance": 0.15},
        ]

    if probability >= 0.7:
        risk_level = "high"
    elif probability >= 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "probability": round(probability, 4),
        "risk_level": risk_level,
        "features": features,
        "top_risk_factors": top_risk_factors,
    }


def _heuristic_risk(features):
    """
    Simple rule-based fallback when we don't have a trained model.
    Weighted combination of the features we know matter most.
    """
    score = 0.0
    score += features["historical_no_show_rate"] * 0.4
    score += min(features["days_until_appointment"] / 60, 1.0) * 0.15
    score += (1 if features["is_monday"] else 0) * 0.1
    score += (0 if features["is_follow_up"] else 0.05)
    if features["past_outreach_count"] == 0:
        score += 0.1
    if features["total_past_appointments"] == 0:
        score += 0.15
    return min(max(score, 0.05), 0.95)
