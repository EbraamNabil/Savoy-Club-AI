
"""Orchestrate a multilingual Award Points conversation."""

import json
import re

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
    """Translate a question and its choices while preserving option IDs."""

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
        if item.get("id") != index or not isinstance(item.get("label"), str):
            raise ValueError("The translated options do not match the source list.")

    return data["question"], translated_options


def start_multilingual_points_flow(llm, initial_message):
    """Start a points flow and ask the first question in the guest's language."""

    language = detect_guest_language(llm, initial_message)
    flow = new_points_flow(language=language)

    return {
        "flow": flow,
        "language": language,
        "question": _get_next_question(llm, flow),
    }


def _get_next_question(llm, flow):
    """Build the next question and translated options."""

    field = get_missing_field(flow)

    if field is None:
        return None

    if field == "nights":
        options = []
    else:
        options = get_available_options(flow, field)

    question, translated_options = _translate_question_and_options(
        llm,
        flow["language"],
        field,
        options,
    )

    if translated_options:
        numbered_options = "\n".join(
            f'{item["id"]}. {item["label"]}'
            for item in translated_options
        )
        return f"{question}\n\n{numbered_options}"

    return question


def process_multilingual_points_answer(llm, flow, answer):
    """Resolve one guest answer, update the flow, and return the next step."""

    field = get_missing_field(flow)

    if field is None:
        return {
            "accepted": False,
            "complete": True,
            "message": generate_guest_message(
                llm,
                flow["language"],
                "This points calculation is already complete.",
            ),
        }

    if field == "nights":
        value = resolve_guest_answer(
            llm=llm,
            answer=answer,
            field="nights",
        )
    else:
        options = get_available_options(flow, field)
        value = resolve_guest_answer(
            llm=llm,
            answer=answer,
            field=field,
            options=options,
        )

    if value is None:
        if field == "nights":
            message = (
                "Please provide a valid positive whole number of nights."
            )
        else:
            message = (
                f"Please choose a valid {FIELD_LABELS[field]} "
                "from the available options."
            )

        return {
            "accepted": False,
            "complete": False,
            "message": generate_guest_message(
                llm,
                flow["language"],
                message,
            ),
            "question": _get_next_question(llm, flow),
        }

    flow[field] = value
    next_field = get_missing_field(flow)

    if next_field is not None:
        return {
            "accepted": True,
            "complete": False,
            "next_field": next_field,
            "question": _get_next_question(llm, flow),
        }

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

    result_message = (
        f"Your estimated Award Points are {result['total_points']} points.\n\n"
        f"{calculation_text}\n\n"
        "For more information, contact the Savoy Club office. "
        "From inside the hotel, call 8080. From outside, call "
        "+20 69 360 2500. The office is available daily from "
        "9:00 AM to 6:00 PM. Contact email: "
        "SavoyClub@savoy-sharm.com."
    )

    localized_result = generate_guest_message(
        llm,
        flow["language"],
        result_message,
    )

    return {
        "accepted": True,
        "complete": True,
        "result": result,
        "message": localized_result,
    }
