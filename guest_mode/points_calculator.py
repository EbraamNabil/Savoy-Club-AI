"""Calculate Savoy Club Award Points using the approved policy table."""

ROOM_POINTS = {
    "Savoy": {
        "Garden View": 180,
        "Pool View": 230,
        "Sea View": 260,
        "Triple Garden View": 250,
        "Diplomatic Suite Garden": 610,
        "Diplomatic Suite Pool": 680,
        "Diplomatic Suite Sea": 770,
        "Presidential Suite": 1080,
    },
    "Royal Savoy": {
        "Royal Savoy Room": 500,
        "Royal Junior Suite": 660,
        "Royal S Suite": 1080,
        "Royal 2-Bedroom Suite": 720,
        "Panoramic Suite": 1080,
        "Villa 2 or 3 Bedrooms": 1800,
        "Villa 4, 5 or 6 Bedrooms": 2700,
    },
    "Sierra": {
        "Garden View": 180,
        "Pool View": 230,
        "Deluxe Garden": 220,
        "Deluxe Pool": 270,
        "Triple Garden": 250,
        "Triple Pool": 300,
        "Suite Garden": 410,
        "Suite Pool": 460,
    },
}

MEAL_POINTS = {
    "Savoy": {
        "Half Board": 80,
        "Half Board Dine Around": 160,
        "Full Board": 160,
        "E-Class - hard": 350,
        "S Class": 420,
    },
    "Royal Savoy": {
        "Half Board": 80,
        "Half Board Dine Around": 160,
        "Full Board": 160,
        "E-Class - hard": 350,
        "S Class": 420,
    },
}


def calculate_award_points(hotel, room_type, meal_plan, nights):
    """Return estimated Award Points for a qualifying stay."""

    if not isinstance(nights, int) or isinstance(nights, bool) or nights <= 0:
        raise ValueError("Nights must be a positive whole number.")

    if hotel not in ROOM_POINTS:
        raise ValueError(f"Unsupported hotel: {hotel}")

    if room_type not in ROOM_POINTS[hotel]:
        raise ValueError(f"Room type '{room_type}' is not listed for {hotel}.")

    room_points = ROOM_POINTS[hotel][room_type]

    # Sierra uses room points only. Meal-plan points are automatically zero.
    if hotel == "Sierra":
        meal_points = 0
        selected_meal_plan = None
    else:
        if meal_plan not in MEAL_POINTS[hotel]:
            raise ValueError(f"Meal plan '{meal_plan}' is not listed for {hotel}.")
        meal_points = MEAL_POINTS[hotel][meal_plan]
        selected_meal_plan = meal_plan

    total_points = (room_points + meal_points) * nights

    return {
        "hotel": hotel,
        "room_type": room_type,
        "room_points_per_night": room_points,
        "meal_plan": selected_meal_plan,
        "meal_points_per_night": meal_points,
        "nights": nights,
        "total_points": total_points,
        "bonus_included": False,
    }
