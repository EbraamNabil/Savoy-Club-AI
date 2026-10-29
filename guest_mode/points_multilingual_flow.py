
"""Orchestrate a multilingual Award Points conversation."""

import json
import re

from guest_mode.points_calculator import ROOM_POINTS, MEAL_POINTS

from guest_mode.points_flow import (
    new_points_flow,
    get_missing_field,
    get_available_options,
    get_points_result,
)
from guest_mode.points_multilingual import (
    detect_guest_language,
    resolve_guest_answer,
    generate_guest_message,
)


FIELD_LABELS = {
    "hotel": "hotel",
    "room_type": "room type",
    "meal_plan": "meal plan",
    "nights": "number of nights",
}



def _translate_question_and_options(llm, language, field, options):
    """Use local English/Arabic templates and Gemini for other languages."""

    language_key = str(language).strip().casefold()

    english_names = {
        "english", "en", "english (us)", "english (uk)"
    }
    arabic_names = {
        "arabic", "ar", "العربية", "عربي", "اللغة العربية"
    }

    if language_key in english_names:
        questions = {
            "hotel": "Which hotel are you staying at?",
            "room_type": "Which room type are you staying in?",
            "meal_plan": "Which meal plan do you have?",
            "nights": "How many nights did you stay?",
        }
        labels = list(options)

    elif language_key in arabic_names:
        questions = {
            "hotel": "في أي فندق تقيم؟",
            "room_type": "ما نوع الغرفة التي تقيم فيها؟",
            "meal_plan": "ما نظام الوجبات الخاص بحجزك؟",
            "nights": "كم ليلة أقمت؟",
        }

        # Translate labels for display only; canonical option values remain unchanged.
        arabic_labels = {
            "Savoy": "سافوي",
            "Royal Savoy": "رويال سافوي",
            "Sierra": "سييرا",
            "Garden View": "إطلالة على الحديقة",
            "Pool View": "إطلالة على حمام السباحة",
            "Sea View": "إطلالة على البحر",
            "Triple Garden View": "غرفة ثلاثية بإطلالة على الحديقة",
            "Diplomatic Suite Garden": "جناح دبلوماسي بإطلالة على الحديقة",
            "Diplomatic Suite Pool": "جناح دبلوماسي بإطلالة على حمام السباحة",
            "Diplomatic Suite Sea": "جناح دبلوماسي بإطلالة على البحر",
            "Presidential Suite": "الجناح الرئاسي",
            "Royal Savoy Room": "غرفة رويال سافوي",
            "Royal Junior Suite": "جناح رويال جونيور",
            "Royal S Suite": "جناح رويال S",
            "Royal 2-Bedroom Suite": "جناح رويال بغرفتي نوم",
            "Panoramic Suite": "الجناح البانورامي",
            "Villa 2 or 3 Bedrooms": "فيلا بغرفتي نوم أو ثلاث غرف نوم",
            "Villa 4, 5 or 6 Bedrooms": "فيلا بأربع أو خمس أو ست غرف نوم",
            "Deluxe Garden": "ديلوكس بإطلالة على الحديقة",
            "Deluxe Pool": "ديلوكس بإطلالة على حمام السباحة",
            "Triple Garden": "غرفة ثلاثية بإطلالة على الحديقة",
            "Triple Pool": "غرفة ثلاثية بإطلالة على حمام السباحة",
            "Suite Garden": "جناح بإطلالة على الحديقة",
            "Suite Pool": "جناح بإطلالة على حمام السباحة",
            "Half Board": "إقامة نصف شاملة",
            "Half Board Dine Around": "إقامة نصف شاملة مع خيارات طعام متنوعة",
            "Full Board": "إقامة كاملة",
            "E-Class - hard": "E-Class - Hard",
            "S Class": "S Class",
        }

        labels = [arabic_labels.get(option, option) for option in options]

    else:
        # Preserve multilingual support through the existing Gemini fallback.
        prompt = f"""
Prepare a guest-facing question in {language}.

Return valid JSON only:
{{
  "question": "translated question",
  "options": [
    {{"id": 1, "label": "translated option"}}
  ]
}}

The options must appear in exactly the same order as the source list.
Use each source option exactly once.
Translate labels naturally, but do not change their meaning.
Do not add or remove options.

Field: {FIELD_LABELS[field]}
Source options:
{json.dumps(options, ensure_ascii=False)}

Question intent:
Ask the guest to select or provide their {FIELD_LABELS[field]}.
"""
        raw = llm.generate_response(prompt).strip()
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)

        if not match:
            raise ValueError("Could not format the translated question.")

        data = json.loads(match.group(0))
        translated_options = data.get("options")

        if not isinstance(data.get("question"), str):
            raise ValueError("The translated question is invalid.")

        if not isinstance(translated_options, list):
            raise ValueError("The translated options are invalid.")

        if len(translated_options) != len(options):
            raise ValueError("The number of translated options changed.")

        for index, item in enumerate(translated_options, start=1):
            if (
                not isinstance(item, dict)
                or item.get("id") != index
                or not isinstance(item.get("label"), str)
            ):
                raise ValueError(
                    "The translated options do not match the source list."
                )

        return data["question"], translated_options

    translated_options = [
        {"id": index, "label": label}
        for index, label in enumerate(labels, start=1)
    ]

    return questions[field], translated_options

def _extract_explicit_fields(llm, flow, message):
    """Extract only fields clearly stated by the guest; validate against canonical options."""
    hotels = list(ROOM_POINTS.keys())
    room_options = {hotel: list(ROOM_POINTS[hotel].keys()) for hotel in hotels}
    meal_options = {hotel: list(MEAL_POINTS.get(hotel, {}).keys()) for hotel in hotels}
    prompt = f"""Extract booking details explicitly stated in this guest message.
Return JSON only with keys hotel, room_type, meal_plan, nights.
Use null for any field not clearly stated. Do not guess or fill missing information.
For hotel, room_type, and meal_plan, values must exactly match the allowed canonical values below.
For nights, return a positive whole-number integer or null. Ignore numbers that are part of room names.
A room type must belong to the selected hotel. A meal plan must belong to the selected hotel.
If hotel is Sierra, meal_plan must be null.
Allowed hotels: {json.dumps(hotels, ensure_ascii=False)}
Room types by hotel: {json.dumps(room_options, ensure_ascii=False)}
Meal plans by hotel: {json.dumps(meal_options, ensure_ascii=False)}
Guest message: {message}
JSON:"""
    try:
        raw = llm.generate_response(prompt).strip()
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            return {}
        data = json.loads(match.group(0))
        if not isinstance(data, dict):
            return {}
    except Exception:
        return {}

    extracted = {}
    hotel = data.get("hotel")
    if isinstance(hotel, str) and hotel in hotels:
        extracted["hotel"] = hotel
    effective_hotel = extracted.get("hotel", flow.get("hotel"))

    room_type = data.get("room_type")
    if effective_hotel and isinstance(room_type, str) and room_type in room_options.get(effective_hotel, []):
        extracted["room_type"] = room_type

    if effective_hotel == "Sierra":
        extracted["meal_plan"] = None
    else:
        meal_plan = data.get("meal_plan")
        if effective_hotel and isinstance(meal_plan, str) and meal_plan in meal_options.get(effective_hotel, []):
            extracted["meal_plan"] = meal_plan

    nights = data.get("nights")
    if isinstance(nights, int) and not isinstance(nights, bool) and nights > 0:
        extracted["nights"] = nights
    return extracted


def _completed_result_message(llm, flow):
    result = get_points_result(flow)

    if result["hotel"] == "Sierra":
        calculation_text = (
            f"Calculation: {result['room_points_per_night']} room points × "
            f"{result['nights']} nights. Meal-plan points: 0."
        )
    else:
        calculation_text = (
            f"Calculation: ({result['room_points_per_night']} room points + "
            f"{result['meal_points_per_night']} meal-plan points) × "
            f"{result['nights']} nights."
        )

    message = (
        f"Your estimated Award Points are {result['total_points']} points.\n\n"
        f"{calculation_text}"
    )
    return generate_guest_message(llm, flow["language"], message)



def start_multilingual_points_flow(llm, initial_message):
    """Start the calculator and fill any booking details explicitly included initially."""
    language = detect_guest_language(llm, initial_message)
    flow = new_points_flow(language=language)
    flow.update(_extract_explicit_fields(llm, flow, initial_message))
    if flow.get("hotel") == "Sierra":
        flow["meal_plan"] = None
    if get_missing_field(flow) is None:
        return {
            "flow": flow,
            "language": language,
            "question": None,
            "complete": True,
            "message": _completed_result_message(llm, flow),
        }
    return {
        "flow": flow,
        "language": language,
        "question": _get_next_question(llm, flow),
        "complete": False,
    }

def process_multilingual_points_answer(llm, flow, answer):
    """Accept multiple explicitly stated fields, ask only for what remains missing."""
    field = get_missing_field(flow)
    if field is None:
        return {
            "accepted": False,
            "complete": True,
            "message": generate_guest_message(
                llm, flow["language"], "This points calculation is already complete."
            ),
        }

    extracted = _extract_explicit_fields(llm, flow, answer)
    # Preserve existing values unless the guest clearly provides a valid replacement.
    for key, value in extracted.items():
        if value is not None or key == "meal_plan":
            flow[key] = value
    if flow.get("hotel") == "Sierra":
        flow["meal_plan"] = None

    # If the message didn't identify the field currently requested, use the existing resolver.
    field = get_missing_field(flow)
    if field is not None:
        if field == "nights":
            value = resolve_guest_answer(llm=llm, answer=answer, field="nights")
        else:
            options = get_available_options(flow, field)
            value = resolve_guest_answer(llm=llm, answer=answer, field=field, options=options)
        if value is not None:
            flow[field] = value
        elif get_missing_field(flow) == field:
            if field == "nights":
                message = "Please provide a valid positive whole number of nights."
            else:
                message = f"Please choose a valid {FIELD_LABELS[field]} from the available options."
            return {
                "accepted": False,
                "complete": False,
                "message": generate_guest_message(llm, flow["language"], message),
                "question": _get_next_question(llm, flow),
            }

    next_field = get_missing_field(flow)
    if next_field is not None:
        return {
            "accepted": True,
            "complete": False,
            "next_field": next_field,
            "question": _get_next_question(llm, flow),
        }

    result = get_points_result(flow)
    localized_result = _completed_result_message(llm, flow)
    return {"accepted": True, "complete": True, "result": result, "message": localized_result}
