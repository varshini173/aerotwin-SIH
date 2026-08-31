"""
Mission Risk / Mission Readiness Assessment
==============================================
Compares the digital twin's current predicted engine capability (RUL,
health, degradation, fault risk) against a user-specified planned mission
(duration + expected load) to produce a mission-risk verdict and a plain
-language recommendation.

This is a prototype decision-support heuristic, not a certified
airworthiness assessment.
"""

from __future__ import annotations

SAFETY_MARGIN = 1.5  # required RUL >= mission_duration * SAFETY_MARGIN for LOW risk
MARGIN_MODERATE = 1.1


def assess_mission(
    rul_hours: float,
    health: float,
    degradation: float,
    fault_risk: float,
    mission_duration_hours: float,
    expected_load_percent: float = 60.0,
) -> dict:
    # Load adjustment: a mission planned at higher-than-baseline load consumes
    # RUL faster, so we discount available RUL proportionally.
    load_factor = 1.0 + max(0.0, (expected_load_percent - 55.0) / 100.0)
    effective_required_hours = mission_duration_hours * load_factor

    required_low = effective_required_hours * SAFETY_MARGIN
    required_moderate = effective_required_hours * MARGIN_MODERATE

    if health < 40 or fault_risk > 70 or rul_hours < required_moderate:
        risk = "HIGH"
    elif health < 70 or fault_risk > 35 or rul_hours < required_low:
        risk = "MODERATE"
    else:
        risk = "LOW"

    readiness = "READY" if risk == "LOW" else ("CAUTION" if risk == "MODERATE" else "NOT READY")

    if risk == "LOW":
        recommendation = "Mission feasible with continued monitoring."
    elif risk == "MODERATE":
        recommendation = (
            "Mission feasible with reduced safety margin — recommend inspection "
            "before flight and close in-flight monitoring."
        )
    else:
        recommendation = "Inspect and service engine before mission. Do not fly with current RUL/health margin."

    return {
        "missionRisk": risk,
        "missionReadiness": readiness,
        "recommendation": recommendation,
        "requiredRulHoursLowRisk": round(required_low, 2),
        "effectiveMissionHours": round(effective_required_hours, 2),
    }
