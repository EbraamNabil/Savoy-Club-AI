from dotenv import load_dotenv
from google import genai

from config import (
    GOOGLE_API_KEY,
    GOOGLE_MODEL,
    LLM_PROVIDER,
    PROJECT_ROOT,
)


# Load environment variables from the project configuration
load_dotenv(PROJECT_ROOT / ".env", override=True)


class LLMProvider:
    """Provide a reusable interface for supported language models."""

    def __init__(self):
        # Validate the selected provider
        if LLM_PROVIDER.lower() != "google":
            raise ValueError(
                f"Unsupported LLM provider: {LLM_PROVIDER}"
            )

        # Ensure the API key is available without displaying it
        if not GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY is missing. Check the project's .env file."
            )

        # Initialize the Gemini client
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self.model_name = GOOGLE_MODEL

    def generate_response(self, prompt: str) -> str:
        """Generate a text response from the configured model."""

        # Send the prompt to Gemini
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )

        # Return the generated text when available
        answer = response.text

        if not answer:
            raise RuntimeError(
                "The language model returned an empty response."
            )

        return answer.strip()
