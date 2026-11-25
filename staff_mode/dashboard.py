import streamlit as st

from common.ticket_service import (
    list_tickets,
    get_ticket_by_id,
    get_ticket_replies,
    update_ticket_status,
    add_ticket_reply,
)


STATUSES = ["Open", "In Progress", "Resolved"]


def _format_ticket(ticket):
    name = ticket.get("guest_name") or "Guest"
    question = ticket.get("guest_question") or ""
    short_question = question[:65]
    if len(question) > 65:
        short_question += "..."

    return f"{name} | {short_question} | {ticket.get('status', 'Open')}"


def _render_ticket_details(ticket):
    ticket_id = str(ticket.get("ticket_id", ""))

    st.divider()
    st.subheader("Ticket Details")

    st.caption(f"Ticket ID: {ticket_id}")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Guest Name**")
        st.write(ticket.get("guest_name") or "Not provided")

        st.write("**Guest Email**")
        st.write(ticket.get("guest_email") or "Not available")

    with col2:
        st.write("**Status**")
        st.write(ticket.get("status", "Open"))

        st.write("**Created At**")
        st.write(ticket.get("created_at", "Not available"))

    st.write("**Guest Question**")
    st.info(ticket.get("guest_question") or "No question available.")

    if ticket.get("consent") and ticket.get("conversation_context"):
        with st.expander("Guest Conversation Context"):
            st.write(ticket["conversation_context"])
    else:
        st.caption("Conversation context was not shared by the guest.")

    st.divider()
    st.subheader("Ticket Replies")

    try:
        replies = get_ticket_replies(ticket_id)

        if not replies:
            st.caption("No replies have been added yet.")
        else:
            for reply in replies:
                with st.container(border=True):
                    st.write(f"**{reply.get('staff_email', 'Staff')}**")
                    st.write(reply.get("reply_text", ""))
                    st.caption(reply.get("created_at", ""))

    except Exception:
        st.error("Could not load ticket replies.")

    st.divider()
    st.subheader("Manage Ticket")

    with st.form(f"status_form_{ticket_id}"):
        current_status = ticket.get("status", "Open")

        if current_status not in STATUSES:
            current_status = "Open"

        new_status = st.selectbox(
            "Update Status",
            STATUSES,
            index=STATUSES.index(current_status),
        )

        status_submitted = st.form_submit_button(
            "Save Status",
            use_container_width=True,
        )

    if status_submitted:
        try:
            updated_ticket = update_ticket_status(ticket_id, new_status)

            if updated_ticket:
                st.success("Ticket status updated successfully.")
                st.rerun()
            else:
                st.error("The ticket could not be updated.")

        except Exception as error:
            print(f"Ticket status update failed: {error!r}")
            st.error("Unable to update ticket status. Please try again.")

    with st.form(f"reply_form_{ticket_id}"):
        reply_text = st.text_area(
            "Your Reply",
            placeholder="Write your response to the guest...",
            height=130,
        )

        reply_submitted = st.form_submit_button(
            "Send Reply",
            type="primary",
            use_container_width=True,
        )

    if reply_submitted:
        staff_email = st.session_state.get("staff_email", "")

        if not reply_text.strip():
            st.warning("Please write a reply before submitting.")
        else:
            try:
                add_ticket_reply(
                    ticket_id=ticket_id,
                    staff_email=staff_email,
                    reply_text=reply_text,
                )
                st.success("Your reply has been saved.")
                st.rerun()

            except Exception as error:
                print(f"Ticket reply failed: {error!r}")
                st.error("Unable to save your reply. Please try again.")


def render_staff_dashboard():
    """Render the staff support ticket dashboard."""

    st.title("SAVOY Club | Staff Dashboard")

    st.success(
        f"Signed in as {st.session_state.get('staff_email', 'Staff')}"
    )

    st.caption("Manage guest support requests and follow up on open tickets.")

    col1, col2 = st.columns([3, 1])

    with col1:
        selected_filter = st.selectbox(
            "Filter Tickets by Status",
            ["All"] + STATUSES,
            key="ticket_status_filter",
        )

    with col2:
        st.write("")
        st.write("")
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    try:
        filter_status = None if selected_filter == "All" else selected_filter
        tickets = list_tickets(status=filter_status, limit=200)

    except Exception as error:
        print(f"Ticket list retrieval failed: {type(error).__name__}: {error}")

        st.error("Unable to load support tickets.")

        # Temporary diagnostic information
        error_message = str(error)[:500]
        error_message = re.sub(
            r"Bearer\s+\S+",
            "Bearer [REDACTED]",
            error_message,
            flags=re.IGNORECASE
        )
        error_message = re.sub(
            r"(sb_secret_|eyJ)[A-Za-z0-9_.-]+",
            "[REDACTED]",
            error_message
        )

        with st.expander("Technical diagnostic details"):
            st.write("Error type:", type(error).__name__)
            st.code(error_message)

        return

    st.subheader("Support Tickets")

    total = len(tickets)
    open_count = sum(1 for t in tickets if t.get("status") == "Open")
    progress_count = sum(
        1 for t in tickets if t.get("status") == "In Progress"
    )
    resolved_count = sum(
        1 for t in tickets if t.get("status") == "Resolved"
    )

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric("Displayed", total)
    metric2.metric("Open", open_count)
    metric3.metric("In Progress", progress_count)
    metric4.metric("Resolved", resolved_count)

    if not tickets:
        st.info("There are no tickets matching this filter.")
        return

    display_rows = []

    for ticket in tickets:
        display_rows.append({
            "Ticket ID": str(ticket.get("ticket_id", "")),
            "Guest": ticket.get("guest_name") or "Guest",
            "Email": ticket.get("guest_email", ""),
            "Question": (ticket.get("guest_question") or "")[:90],
            "Status": ticket.get("status", ""),
            "Created At": ticket.get("created_at", ""),
        })

    st.dataframe(
        display_rows,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.subheader("Open a Ticket")

    ticket_lookup = {
        str(ticket["ticket_id"]): ticket
        for ticket in tickets
        if ticket.get("ticket_id")
    }

    ticket_ids = list(ticket_lookup.keys())

    selected_ticket_id = st.selectbox(
        "Select a ticket to view its details",
        options=ticket_ids,
        format_func=lambda ticket_id: _format_ticket(
            ticket_lookup[ticket_id]
        ),
        key="selected_ticket_id",
    )

    if selected_ticket_id:
        try:
            selected_ticket = get_ticket_by_id(selected_ticket_id)

            if selected_ticket:
                _render_ticket_details(selected_ticket)
            else:
                st.warning("This ticket could not be found.")

        except Exception as error:
            print(f"Ticket details retrieval failed: {error!r}")
            st.error("Unable to load ticket details.")
