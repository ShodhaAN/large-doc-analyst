import httpx
import logging
from typing import Optional
from backend.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Connects to Ollama running locally on your computer.
    Sends prompts to Llama 3 and gets answers back.
    """

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        logger.info(f"OllamaClient ready: {self.model} at {self.base_url}")

    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> str:
        """
        Send a prompt to Llama 3 and get a response.

        Args:
            prompt: The full prompt including context and question
            temperature: How creative the response is (0=focused, 1=creative)
            max_tokens: Maximum length of response

        Returns:
            The AI's response as a string
        """
        logger.info(f"Sending prompt to {self.model}...")

        try:
            # Send request to Ollama API
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=120.0  # 2 minute timeout
            )

            response.raise_for_status()
            result = response.json()

            answer = result.get("response", "").strip()
            logger.info(f"Got response: {len(answer)} characters")
            return answer

        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama!")
            raise ConnectionError(
                "Cannot connect to Ollama. "
                "Make sure Ollama is running: open a terminal and run 'ollama serve'"
            )
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise

    def is_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = httpx.get(
                f"{self.base_url}/api/tags",
                timeout=5.0
            )
            return response.status_code == 200
        except:
            return False


# One shared instance
ollama_client = OllamaClient()