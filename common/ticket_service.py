from datetime import datetime, timezone

from common.supabase_client import get_supabase_client


VALID_STATUSES = {"Open", "In Progress", "Resolved"}


def _get_client():
    return get_supabase_client()


def _first_row(response):
    """Return the first database row or None."""
    rows = response.data or []

    if isinstance(rows, dict):
        return rows

    return rows[0] if rows else None


def create_ticket(
    guest_email,
    guest_question,
    guest_name=None,
    conversation_context=None,
    consent=False,
):
    """Create a support ticket for a guest."""

    email = (guest_email or "").strip().lower()
    question = (guest_question or "").strip()

    if not email:
        raise ValueError("Guest email is required.")

    if not question:
        raise ValueError("Guest question is required.")

    ticket_data = {
        "guest_email": email,
        "guest_question": question,
        "guest_name": (guest_name or "").strip() or None,
        "consent": bool(consent),
        "conversation_context": (
            conversation_context if consent else None
        ),
        "status": "Open",
    }

    response = (
        _get_client()
        .table("tickets")
        .insert(ticket_data)
        .execute()
    )

    ticket = _first_row(response)

    if not ticket:
        raise RuntimeError("Ticket creation did not return a record.")

    return ticket


def get_ticket_by_id(ticket_id):
    """Get a ticket by ID. Intended for authenticated staff use."""

    ticket_id = (ticket_id or "").strip()

    if not ticket_id:
        return None

    response = (
        _get_client()
        .table("tickets")
        .select("*")
        .eq("ticket_id", ticket_id)
        .limit(1)
        .execute()
    )

    return _first_row(response)


def get_guest_ticket(ticket_id, guest_email):
    """
    Get a guest ticket only when both ticket ID and email match.
    Returns None if the pair does not match.
    """

    ticket_id = (ticket_id or "").strip()
    email = (guest_email or "").strip().lower()

    if not ticket_id or not email:
        return None

    response = (
        _get_client()
        .table("tickets")
        .select("*")
        .eq("ticket_id", ticket_id)
        .eq("guest_email", email)
        .limit(1)
        .execute()
    )

    return _first_row(response)


def list_tickets(status=None, limit=100):
    """List tickets for the staff dashboard, newest first."""

    if status is not None and status not in VALID_STATUSES:
        raise ValueError("Invalid ticket status.")

    limit = max(1, min(int(limit), 500))

    query = (
        _get_client()
        .table("tickets")
        .select("*")
    )

    if status:
        query = query.eq("status", status)

    response = (
        query
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return response.data or []


def get_ticket_replies(ticket_id):
    """Get all replies for a ticket, oldest first."""

    ticket_id = (ticket_id or "").strip()

    if not ticket_id:
        return []

    response = (
        _get_client()
        .table("ticket_replies")
        .select("*")
        .eq("ticket_id", ticket_id)
        .order("created_at", desc=False)
        .execute()
    )

    return response.data or []


def update_ticket_status(ticket_id, new_status):
    """Update a ticket status and its updated_at timestamp."""

    ticket_id = (ticket_id or "").strip()

    if new_status not in VALID_STATUSES:
        raise ValueError("Invalid ticket status.")

    if not ticket_id:
        raise ValueError("Ticket ID is required.")

    response = (
        _get_client()
        .table("tickets")
        .update({
            "status": new_status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        .eq("ticket_id", ticket_id)
        .select("*")
        .execute()
    )

    return _first_row(response)


def add_ticket_reply(ticket_id, staff_email, reply_text):
    """Save a staff reply and update the ticket modification time."""

    ticket_id = (ticket_id or "").strip()
    email = (staff_email or "").strip().lower()
    message = (reply_text or "").strip()

    if not ticket_id:
        raise ValueError("Ticket ID is required.")

    if not email:
        raise ValueError("Staff email is required.")

    if not message:
        raise ValueError("Reply text cannot be empty.")

    # Confirm that the ticket exists before inserting a reply.
    ticket = get_ticket_by_id(ticket_id)

    if not ticket:
        raise ValueError("Ticket was not found.")

    response = (
        _get_client()
        .table("ticket_replies")
        .insert({
            "ticket_id": ticket_id,
            "staff_email": email,
            "reply_text": message,
        })
        .execute()
    )

    reply = _first_row(response)

    if not reply:
        raise RuntimeError("Reply creation did not return a record.")

    # Keep the ticket's updated_at timestamp in sync with its replies.
    (
        _get_client()
        .table("tickets")
        .update({
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        .eq("ticket_id", ticket_id)
        .execute()
    )

    return reply
