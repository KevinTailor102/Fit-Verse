"""
FitVerse — IBM watsonx.ai Granite Client
Supports both IBM Cloud (cloud.ibm.com) and Cloud Pak for Data (CPD/dai.cloud.ibm.com)
"""
import os
import logging
from typing import List, Dict, Optional

from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from agent_instructions import build_system_prompt

logger = logging.getLogger(__name__)


def _build_credentials(api_key: str, url: str) -> Credentials:
    """
    Build Credentials object.
    - IBM Cloud (us-south.ml.cloud.ibm.com, etc.)  → api_key only
    - Cloud Pak for Data (*.dai.cloud.ibm.com)      → username + api_key + version
    """
    cpd_url = "dai.cloud.ibm.com" in url or "cp4d" in url or "cpd" in url
    if cpd_url:
        version  = os.environ.get("WATSONX_CPD_VERSION", "5.1")
        username = os.environ.get("WATSONX_USERNAME", "admin")
        logger.info("Detected Cloud Pak for Data URL — using username=%s version=%s", username, version)
        return Credentials(api_key=api_key, url=url, username=username, version=version)
    return Credentials(api_key=api_key, url=url)


class WatsonxClient:
    """Wraps IBM watsonx.ai ModelInference for FitVerse chat completions."""

    def __init__(self, api_key: str, project_id: str, url: str, model_id: str):
        self.model_id = model_id
        self.project_id = project_id
        credentials = _build_credentials(api_key, url)
        self.model = ModelInference(
            model_id=model_id,
            credentials=credentials,
            project_id=project_id,
            params={
                GenParams.MAX_NEW_TOKENS: 1024,
                GenParams.TEMPERATURE: 0.7,
                GenParams.TOP_P: 0.9,
                GenParams.REPETITION_PENALTY: 1.1,
            },
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        user_profile: Optional[Dict] = None,
        max_tokens: int = 1024,
    ) -> str:
        """
        Send a conversation history using the modern chat API.

        Args:
            messages: list of {"role": "user"|"assistant", "content": "..."}
            user_profile: optional user dict for personalised system prompt
            max_tokens: maximum tokens to generate

        Returns:
            Assistant reply string
        """
        system_prompt = build_system_prompt(user_profile)

        # Build messages list with system prompt for chat API
        chat_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant"):
                chat_messages.append({"role": role, "content": content})

        try:
            response = self.model.chat(
                messages=chat_messages,
                params={GenParams.MAX_NEW_TOKENS: max_tokens},
            )
            reply = (
                response.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            return reply if reply else "I'm having trouble responding right now. Please try again."
        except Exception as exc:
            logger.error("watsonx.ai error: %s", exc)
            # Fallback to generate_text if chat API fails
            try:
                prompt = f"<|system|>\n{system_prompt}\n"
                for msg in messages:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        prompt += f"<|user|>\n{content}\n"
                    elif role == "assistant":
                        prompt += f"<|assistant|>\n{content}\n"
                prompt += "<|assistant|>\n"
                response = self.model.generate_text(
                    prompt=prompt,
                    params={GenParams.MAX_NEW_TOKENS: max_tokens},
                )
                return response.strip() if response else "I'm having trouble responding right now."
            except Exception as exc2:
                logger.error("watsonx.ai fallback error: %s", exc2)
                return (
                    "⚠️ I'm temporarily unavailable. Please check your IBM watsonx.ai credentials "
                    "and try again. If the issue persists, verify your API key and project ID in the .env file."
                )

    def generate_workout_plan(self, user_profile: Dict, goal: str, level: str, days: int) -> str:
        """Generate a structured workout plan."""
        return self.chat(
            [{"role": "user", "content": (
                f"Create a detailed {days}-day/week {level} {goal} workout plan for me. "
                f"Include exercises, sets, reps, rest periods, warm-up, and cool-down. "
                f"Format it clearly with day-by-day breakdown and exercise descriptions."
            )}],
            user_profile=user_profile,
            max_tokens=1500,
        )

    def generate_meal_plan(self, user_profile: Dict, goal: str, calories: int, diet_type: str) -> str:
        """Generate a personalised meal plan."""
        return self.chat(
            [{"role": "user", "content": (
                f"Create a 7-day {diet_type} meal plan targeting {calories} kcal/day for {goal}. "
                f"Include breakfast, lunch, dinner, and 2 snacks with calorie and macro estimates. "
                f"Use Indian food options where possible and include easy recipes."
            )}],
            user_profile=user_profile,
            max_tokens=2000,
        )

    def get_fitness_tip(self, user_profile: Dict) -> str:
        """Return a quick personalised fitness tip."""
        return self.chat(
            [{"role": "user", "content": "Give me one specific fitness tip for today based on my profile. Keep it under 100 words."}],
            user_profile=user_profile,
            max_tokens=150,
        )


_client_instance: Optional[WatsonxClient] = None


def get_watsonx_client() -> Optional[WatsonxClient]:
    """Return a singleton WatsonxClient, or None if credentials are missing."""
    global _client_instance
    if _client_instance is not None:
        return _client_instance

    api_key = os.environ.get("WATSONX_API_KEY", "").strip()
    project_id = os.environ.get("WATSONX_PROJECT_ID", "").strip()
    url = os.environ.get("WATSONX_URL", "https://us-south.ml.cloud.ibm.com").rstrip("/")
    model_id = os.environ.get("WATSONX_MODEL_ID", "ibm/granite-13b-chat-v2").strip()

    if not api_key or not project_id:
        logger.warning(
            "WATSONX_API_KEY or WATSONX_PROJECT_ID not set — AI features will be disabled."
        )
        return None

    # Skip obviously placeholder values
    if "your-ibm" in api_key or "dummy" in api_key:
        logger.warning("WATSONX_API_KEY appears to be a placeholder — AI features disabled.")
        return None

    try:
        _client_instance = WatsonxClient(api_key, project_id, url, model_id)
        logger.info("watsonx.ai client initialised with model: %s", model_id)
        return _client_instance
    except Exception as exc:
        logger.error("Failed to initialise watsonx.ai client: %s", exc)
        return None
