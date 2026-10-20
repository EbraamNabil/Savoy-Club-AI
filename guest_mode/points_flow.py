"""Manage the interactive Award Points calculation flow."""

from guest_mode.points_calculator import (
    ROOM_POINTS,
    MEAL_POINTS,
    calculate_award_points,
)


def new_points_flow(language="en"):
    """Create a fresh points-calculation session."""
    return {
        "active": True,
        "language": language,
        "hotel": None,
        "room_type": None,
        "meal_plan": None,
        "nights": None,
    }


def get_missing_field(flow):
    """Skip meal-plan selection for Sierra."""
    if flow.get("hotel") == "Sierra":
        required_fields = ("hotel", "room_type", "nights")
    else:
        required_fields = ("hotel", "room_type", "meal_plan", "nights")

    for field in required_fields:
        if flow.get(field) is None:
            return field
    return None


def get_available_options(flow, field):
    """Return valid options for the requested field."""
    hotel = flow.get("hotel")

    if field == "hotel":
        return list(ROOM_POINTS.keys())

    if field == "room_type" and hotel in ROOM_POINTS:
        return list(ROOM_POINTS[hotel].keys())

    if field == "meal_plan" and hotel in MEAL_POINTS:
        return list(MEAL_POINTS[hotel].keys())

    return []


def get_points_result(flow):
    """Calculate points when all required information is available."""
    missing_field = get_missing_field(flow)

    if missing_field is not None:
        raise ValueError(f"Missing required field: {missing_field}")

    return calculate_award_points(
        hotel=flow["hotel"],
        room_type=flow["room_type"],
        meal_plan=flow.get("meal_plan"),
        nights=flow["nights"],
    )
