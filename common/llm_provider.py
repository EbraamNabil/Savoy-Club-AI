
from dotenv import load_dotenv
from openai import OpenAI

from config import (
    LLM_PROVIDER,
    PROJECT_ROOT,
    GROQ_API_KEY,
    GROQ_MODEL,
)

load_dotenv(PROJECT_ROOT / ".env", override=True)


class LLMProvider:
    """Provide a reusable interface for the configured language model."""

    def __init__(self):
        self.provider = LLM_PROVIDER.lower()

        if self.provider == "groq":
            if not GROQ_API_KEY:
                raise ValueError(
                    "GROQ_API_KEY is missing. Configure it in "
                    "Streamlit secrets or environment variables."
                )

            self.client = OpenAI(
                api_key=GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1",
            )
            self.model_name = GROQ_MODEL

        else:
            raise ValueError(
                f"Unsupported LLM provider: {self.provider}. "
                "This deployment currently supports groq."
            )

    def generate_response(self, prompt: str) -> str:
        """Generate a text response from Groq."""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful Savoy Club assistant. "
                        "Answer clearly using the provided context. "
                        "Never invent hotel policies."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=512,
            temperature=0.2,
        )

        answer = response.choices[0].message.content

        if not answer or not answer.strip():
            raise RuntimeError(
                "The language model returned an empty response."
            )

        return answer.strip()
