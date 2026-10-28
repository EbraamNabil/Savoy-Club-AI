
import base64
import streamlit as st

from config import PROJECT_ROOT
from guest_mode.chatbot import get_guest_chatbot
from common.llm_provider import LLMProvider
from guest_mode.points_multilingual_flow import (
    start_multilingual_points_flow,
    process_multilingual_points_answer,
)
import re



POINTS_BALANCE_MESSAGE = (
    "For any inquiries about **SAVOY Club**, points collection, "
    "redemption, or your account balance, please contact us at "
    "**Ext. 8080** from inside the hotel or "
    "**+20 69 360 2500 (Ext. 2)** from outside.\n\n"
    "You can also visit the **SAVOY Club Desk daily from "
    "10:00 AM to 6:00 PM** for personalized assistance.\n\n"
    "For more information, visit "
    "[www.savoy-sharm.com/savoy-club/]"
    "(http://www.savoy-sharm.com/savoy-club/) or email "
    "**SavoyClub@savoy-sharm.com**."
)


def is_points_balance_inquiry(question: str) -> bool:
    """Detect requests for a member's existing points balance."""
    text = question.casefold()

    patterns = [
        r"\bpoint balance\b",
        r"\bpoints balance\b",
        r"\baccount balance\b",
        r"\bbalance of my points\b",
        r"\bhow many points do i have\b",
        r"\bcheck my points\b",
        r"\bmy points balance\b",
        r"\bرصيد النقاط\b",
        r"\رصيدي\b",
        r"\bرصيدى\b",
        r"\bكم نقطة عندي\b",
        r"\bكام نقطة عندي\b",
        r"\bбаланс баллов\b",
        r"\bsolde de points\b",
        r"\bsaldo punti\b",
    ]

    return any(re.search(pattern, text) for pattern in patterns)


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Savoy Club | Guest Assistant",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------
# Brand assets
# ---------------------------------------------------------
ASSETS_DIR = PROJECT_ROOT / "assets"
LOGO_PATH = ASSETS_DIR / "savoy_logo.png"
BACKGROUND_PATH = ASSETS_DIR / "1.png"


def get_background_data_uri():
    """Return the local background image as an embedded data URI."""
    if not BACKGROUND_PATH.exists():
        return ""

    encoded_image = base64.b64encode(
        BACKGROUND_PATH.read_bytes()
    ).decode("utf-8")

    return f"data:image/png;base64,{encoded_image}"


# ---------------------------------------------------------
# Luxury navy-and-gold theme
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url(
      'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap'
    );

    :root {
        --navy: #06172D;
        --navy-light: #0B2341;
        --gold: #D9B56D;
        --gold-light: #F3DCA5;
        --text: #F7F3EA;
        --muted: #A9B5C6;
    }

    .stApp {
        background: linear-gradient(145deg, #06172D, #030D1A);
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stMainBlockContainer"] {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1250px;
    }

    h1, h2, h3 {
        color: var(--gold-light) !important;
        font-family: 'Cormorant Garamond', Georgia, serif !important;
    }

    p, label, .stMarkdown {
        color: var(--text);
    }

    /* Home page brand styles */
    .brand-eyebrow {
        color: var(--gold);
        text-transform: uppercase;
        letter-spacing: 4px;
        font-size: 0.68rem;
        font-weight: 600;
        text-align: center;
    }

    .hero-title {
        color: var(--gold-light);
        font-family: 'Cormorant Garamond', Georgia, serif;
        font-size: clamp(2.5rem, 5vw, 4.5rem);
        line-height: 1.05;
        text-align: center;
        font-weight: 600;
        margin: 0.45rem 0;
        text-shadow: 0 2px 16px rgba(0, 0, 0, 0.5);
    }

    .hero-subtitle {
        color: #E0E5ED;
        text-align: center;
        font-size: 0.72rem;
        letter-spacing: 3px;
        line-height: 1.8;
        text-transform: uppercase;
        text-shadow: 0 2px 10px #000;
    }

    .gold-divider {
        width: 105px;
        height: 1px;
        margin: 1rem auto;
        background: linear-gradient(
            90deg, transparent, var(--gold), transparent
        );
    }

    .section-caption {
        color: #F2E8D5;
        text-align: center;
        font-family: 'Cormorant Garamond', Georgia, serif;
        font-size: 1.05rem;
        margin-bottom: 1.1rem;
        text-shadow: 0 2px 8px #000;
    }

    .mode-card {
        min-height: 185px;
        height: 100%;
        padding: 1.1rem 1rem;
        border: 1px solid rgba(217, 181, 109, 0.72);
        border-radius: 16px;
        background: linear-gradient(
            145deg,
            rgba(5, 24, 46, 0.94),
            rgba(3, 15, 30, 0.96)
        );
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
        text-align: center;
        box-sizing: border-box;
    }

    .mode-card.guest-card {
        border: 1.5px solid #E4B85D;
        box-shadow:
            0 0 18px rgba(217, 181, 109, 0.22),
            0 12px 32px rgba(0, 0, 0, 0.3);
    }

    .mode-icon {
        color: var(--gold);
        line-height: 1;
        margin: 0 auto 0.55rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .mode-icon svg {
        width: 38px;
        height: 38px;
        display: block;
    }

    .mode-title {
        font-family: 'Cormorant Garamond', Georgia, serif;
        font-size: 1.8rem;
        color: var(--gold-light);
        font-weight: 600;
        margin-bottom: 0.25rem;
    }

    .mode-description {
        color: #DCE3EC;
        font-size: 0.8rem;
        line-height: 1.55;
    }

    /* Shared buttons */
    .stButton > button {
        border-radius: 10px;
        border: 1px solid rgba(217, 181, 109, 0.7);
        background: rgba(6, 23, 45, 0.95);
        color: var(--gold-light);
        font-weight: 600;
        min-height: 42px;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        border-color: var(--gold-light) !important;
        background: #173653 !important;
        color: #F2E8D5 !important;
        -webkit-text-fill-color: #F2E8D5 !important;
        box-shadow: 0 0 18px rgba(217, 181, 109, 0.2);
    }

    .stButton > button[kind="primary"],
    .stButton [data-testid="stBaseButton-primary"] {
        background: linear-gradient(115deg, #B98B3F, #F0D69A);
        color: #07172A;
        border: 1px solid #F0D69A;
    }

    .stButton > button[kind="primary"],
    .stButton [data-testid="stBaseButton-primary"]:hover,
    .stButton > button[kind="primary"],
    .stButton [data-testid="stBaseButton-primary"]:focus,
    .stButton > button[kind="primary"],
    .stButton [data-testid="stBaseButton-primary"]:active {
        background: linear-gradient(115deg, #D0A75C, #FFE7AE) !important;
        color: #07172A !important;
        -webkit-text-fill-color: #07172A !important;
        border-color: #FFE7AE !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #06172D 0%, #091E35 100%);
        border-right: 1px solid rgba(217, 181, 109, 0.25);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #E6EAF0;
    }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        border: 1px solid rgba(217, 181, 109, 0.12);
        border-radius: 16px;
        padding: 0.9rem 1rem;
        background: rgba(14, 37, 62, 0.58);
    }


    /* Chat input: remove the white outer area */
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div {
        background: #07182A !important;
        background-color: #07182A !important;
        box-shadow: none !important;
    }

    [data-testid="stChatInput"] {
        border: 1px solid #C9A45C !important;
        border-radius: 16px !important;
        overflow: hidden !important;
    }

    [data-testid="stChatInput"] textarea {
        background: #07182A !important;
        color: #F2E8D5 !important;
        -webkit-text-fill-color: #F2E8D5 !important;
        caret-color: #D8B36A !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #C8D2DF !important;
        -webkit-text-fill-color: #C8D2DF !important;
        opacity: 1 !important;
    }

    [data-testid="stChatInput"] button {
        background: #C9A45C !important;
        color: #07182A !important;
        border: 1px solid #C9A45C !important;
    }

    /* Chat input */
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div {
        background: #0B1F33 !important;
        border: 1px solid #C9A45C !important;
        border-radius: 16px !important;
        box-shadow: none !important;
    }

    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInput"] textarea:focus {
        background-color: #0B1F33 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        caret-color: #D8B36A !important;
        border: none !important;
        box-shadow: none !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #B8C5D6 !important;
        -webkit-text-fill-color: #B8C5D6 !important;
        opacity: 1 !important;
    }

    [data-testid="stChatInput"] button {
        background: #C9A45C !important;
        color: #07182A !important;
        border: 1px solid #C9A45C !important;
        border-radius: 10px !important;
    }

    [data-testid="stChatInput"] button svg {
        color: #07182A !important;
        fill: #07182A !important;
    }

    [data-testid="stExpander"] {
        border: 1px solid rgba(217, 181, 109, 0.28);
        border-radius: 12px;
        background: rgba(8, 28, 49, 0.7);
    }

    .chat-heading {
        font-family: 'Cormorant Garamond', Georgia, serif;
        font-size: 2.7rem;
        font-weight: 600;
        color: var(--gold-light);
        line-height: 1.1;
    }

    .chat-subheading {
        color: #AEBBCC;
        font-size: 0.91rem;
        line-height: 1.7;
    }

    .footer-note {
        color: #E1D3B8;
        text-align: center;
        font-size: 0.67rem;
        letter-spacing: 2px;
        margin-top: 1.8rem;
        text-shadow: 0 2px 8px #000;
    }

    hr {
        border-color: rgba(217, 181, 109, 0.18);
    }

    @media (max-width: 768px) {
        .hero-subtitle {
            letter-spacing: 1.5px;
            font-size: 0.65rem;
        }

        .mode-card {
            min-height: 180px;
            padding: 0.9rem 0.6rem;
        }

        .mode-title {
            font-size: 1.5rem;
        }

        .mode-description {
            font-size: 0.72rem;
        }

        .chat-heading {
            font-size: 2.2rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "chats" not in st.session_state:
    st.session_state.chats = []

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None


def create_new_chat():
    """Create and select a new conversation."""
    import uuid

    chat = {
        "id": str(uuid.uuid4()),
        "title": "New conversation",
        "messages": [],
        "points_flow": None,
    }

    st.session_state.chats.insert(0, chat)
    st.session_state.active_chat_id = chat["id"]


def get_active_chat():
    """Return the selected conversation, if one exists."""
    for chat in st.session_state.chats:
        if chat["id"] == st.session_state.active_chat_id:
            return chat

    return None


def render_logo(width=150):
    """Display the official logo when available, otherwise use text."""
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=width)
    else:
        st.markdown(
            """
            <div style="text-align:center; line-height:1.0;">
                <div style="
                    color:#E5C47D;
                    font-family:'Cormorant Garamond',Georgia,serif;
                    font-size:2.8rem;
                ">S</div>
                <div style="
                    color:#F3DCA5;
                    font-family:'Cormorant Garamond',Georgia,serif;
                    font-size:1.65rem;
                    letter-spacing:4px;
                ">SAVOY</div>
                <div style="
                    color:#D9B56D;
                    font-size:0.6rem;
                    letter-spacing:6px;
                ">CLUB</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------
# Home page
# ---------------------------------------------------------
def render_home():
    """Render the landing page over the resort background."""

    background_uri = get_background_data_uri()

    # The image is embedded into the page so it works in Streamlit.
    if background_uri:
        st.markdown(
            f"""
            <style>
            [data-testid="stAppViewContainer"] {{
                background:
                    linear-gradient(
                        180deg,
                        rgba(3, 15, 32, 0.16) 0%,
                        rgba(3, 15, 32, 0.12) 42%,
                        rgba(3, 15, 32, 0.42) 100%
                    ),
                    url("{background_uri}") center center / cover no-repeat fixed
                    !important;
            }}

            [data-testid="stMain"] {{
                background: transparent !important;
            }}

            [data-testid="stMainBlockContainer"] {{
                max-width: 1000px;
                padding-top: 0.8rem;
                padding-bottom: 1rem;
            }}

            [data-testid="stHeader"] {{
                background: transparent !important;
            }}

            [data-testid="stBottom"] {{
                background: transparent !important;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    # Compact luxury navigation line
    nav_left, nav_right = st.columns([3, 2])

    with nav_left:
        st.markdown(
            """
            <div style="
                color:#F3DCA5;
                font-size:0.62rem;
                letter-spacing:3px;
                padding-top:0.6rem;
                text-shadow:0 2px 8px #000;
            ">SAVOY CLUB</div>
            """,
            unsafe_allow_html=True,
        )

    with nav_right:
        st.markdown(
            """
            <div style="
                color:#F3DCA5;
                font-size:0.55rem;
                letter-spacing:2px;
                text-align:right;
                padding-top:0.6rem;
                text-shadow:0 2px 8px #000;
            ">LUXURY · MEMBERSHIP · EXCLUSIVE BENEFITS</div>
            """,
            unsafe_allow_html=True,
        )

    # Centered brand and welcome message
    st.markdown(
        '<div style="height:0.25rem"></div>',
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 1.5, 1])

    with center:
        render_logo(width=115)

        st.markdown(
            '<div class="hero-title">Welcome to Savoy Club</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="hero-subtitle">'
            'Your exclusive membership experience'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="gold-divider"></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-caption">Choose your mode to continue</div>',
            unsafe_allow_html=True,
        )

    # Two interactive mode cards
    card_left, card_right = st.columns(2, gap="medium")

    with card_left:
        st.markdown(
            """
            <div class="mode-card guest-card">
                <div class="mode-icon" aria-label="Guest account"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="3.5" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M5 20c.5-4 3-6 7-6s6.5 2 7 6" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg></div>
                <div class="mode-title">Guest Mode</div>
                <div class="mode-description">
                    Ask about membership rules,<br>
                    benefits, points, and rewards.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "➜",
            type="primary",
            use_container_width=True,
            key="enter_guest",
        ):
            if not st.session_state.chats:
                create_new_chat()

            st.session_state.page = "guest"
            st.rerun()

    with card_right:
        st.markdown(
            """
            <div class="mode-card">
                <div class="mode-icon" aria-label="Staff dashboard"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4" width="17" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M7 15v-3m5 3V8m5 7v-5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg></div>
                <div class="mode-title">Staff Mode</div>
                <div class="mode-description">
                    Access analytics and insights<br>
                    <span style="color:#D9B56D;">Dashboard coming soon</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.button(
            "➜",
            use_container_width=True,
            disabled=True,
            key="staff_inactive",
            help="Staff Mode is coming soon",
        )

    st.markdown(
        """
        <div class="footer-note">
            SAVOY CLUB · YOUR STAY, YOUR REWARDS, YOUR EXPERIENCE
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Guest chat page
# ---------------------------------------------------------
def render_guest():
    """Render the chat workspace and its conversation sidebar."""

    with st.sidebar:
        render_logo(width=125)

        st.markdown(
            '<div class="brand-eyebrow">Guest Assistant</div>',
            unsafe_allow_html=True,
        )

        st.divider()

        if st.button(
            "＋  New Chat",
            type="primary",
            use_container_width=True,
            key="new_chat",
        ):
            create_new_chat()
            st.rerun()

        if st.button(
            "←  Back to Home",
            use_container_width=True,
            key="back_home",
        ):
            st.session_state.page = "home"
            st.rerun()

        st.markdown("### Chat History")

        if not st.session_state.chats:
            st.caption("Your conversations will appear here.")

        for chat_item in st.session_state.chats:
            is_active = (
                chat_item["id"] == st.session_state.active_chat_id
            )

            button_label = (
                f"●  {chat_item['title']}"
                if is_active
                else f"   {chat_item['title']}"
            )

            if st.button(
                button_label,
                use_container_width=True,
                key=f"select_chat_{chat_item['id']}",
            ):
                st.session_state.active_chat_id = chat_item["id"]
                st.rerun()

        st.divider()
        st.caption("Powered by Savoy Club AI")

    chat = get_active_chat()

    if chat is None:
        create_new_chat()
        st.rerun()

    header_left, header_right = st.columns([5, 1])

    with header_left:
        st.markdown(
            '<div class="chat-heading">Guest Assistant</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="chat-subheading">'
            'Your personal guide to Savoy Club membership rules, '
            'benefits, points, and rewards.'
            '</div>',
            unsafe_allow_html=True,
        )

    with header_right:
        if st.button(
            "Clear Chat",
            use_container_width=True,
            key="clear_chat",
        ):
            chat["messages"] = []
            chat["points_flow"] = None
            chat["title"] = "New conversation"
            st.rerun()

    st.divider()

    if not chat["messages"]:
        st.markdown(
            """
            <div style="text-align:center;padding:2.5rem 1rem 1rem;">
                <div style="
                    color:#D9B56D;
                    font-size:2.4rem;
                    margin-bottom:0.5rem;
                ">✧</div>
                <div style="
                    color:#F3DCA5;
                    font-family:'Cormorant Garamond',Georgia,serif;
                    font-size:2rem;
                ">How may we assist you?</div>
                <div style="color:#A9B5C6;margin-top:0.5rem;">
                    Ask anything about the official Savoy Club policy.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        suggestion_columns = st.columns(3)

        suggestions = [
            "What are the requirements for Gold membership?",
            "How do I earn award points?",
            "How early must I book a free room night?",
        ]

        for index, suggestion in enumerate(suggestions):
            with suggestion_columns[index]:
                if st.button(
                    suggestion,
                    use_container_width=True,
                    key=f"suggestion_{index}",
                ):
                    chat["pending_question"] = suggestion
                    st.rerun()

    # Display conversation history
    for message in chat["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            

    pending_question = chat.pop("pending_question", None)

    question = st.chat_input(
        "Ask about membership, points, benefits, or rewards..."
    )

    question = question or pending_question

    if question:
        chat["messages"].append({
            "role": "user",
            "content": question,
        })

        if chat["title"] == "New conversation":
            chat["title"] = (
                question[:35] + "..."
                if len(question) > 35
                else question
            )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner(
                "Reviewing the official Savoy Club policy..."
            ):
                try:
                    # Continue an existing points conversation first.
                    if chat.get("points_flow") is not None:
                        llm = LLMProvider()
                        outcome = process_multilingual_points_answer(
                            llm,
                            chat["points_flow"],
                            question,
                        )

                        if outcome.get("complete"):
                            answer = outcome.get(
                                "message",
                                "The points calculation is complete.",
                            )
                            chat["points_flow"] = None
                        else:
                            parts = []

                            if outcome.get("message"):
                                parts.append(outcome["message"])

                            if outcome.get("question"):
                                parts.append(outcome["question"])

                            answer = "\n\n".join(parts)

                        sources = []

                    # Start the calculator only for explicit calculation requests.
                    elif is_points_calculation_request(question):
                        llm = LLMProvider()
                        outcome = start_multilingual_points_flow(
                            llm,
                            question,
                        )

                        chat["points_flow"] = outcome["flow"]
                        answer = outcome["question"]
                        sources = []

                    # Keep all other questions on the existing policy RAG path.
                    else:
                        chatbot = get_guest_chatbot()
                        result = chatbot.answer_question(question)

                        answer = result["answer"]
                        sources = result["sources"]

                    st.markdown(answer)

                    
                    

                    chat["messages"].append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    })

                except Exception as error:
                    # Keep technical details in the server log only.
                    import traceback
                    print(f"Guest chatbot error: {error!r}")
                    traceback.print_exc()

                    error_text = repr(error).casefold()
                    if (
                        "503" in error_text
                        or "unavailable" in error_text
                        or "high demand" in error_text
                    ):
                        friendly_error = (
                            "The AI service is temporarily busy. "
                            "Please try your question again in a minute."
                        )
                    else:
                        friendly_error = (
                            "We couldn't process your question right now. "
                            "Please try again later."
                        )

                    st.warning(friendly_error)

                    chat["messages"].append({
                        "role": "assistant",
                        "content": friendly_error,
                        "sources": [],
                    })

        st.rerun()


# ---------------------------------------------------------
# Application routing
# ---------------------------------------------------------
if st.session_state.page == "home":
    render_home()
else:
    render_guest()
