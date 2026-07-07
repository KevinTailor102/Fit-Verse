"""
FitVerse — IBM watsonx.ai Granite Client
Supports both IBM Cloud (cloud.ibm.com) and Cloud Pak for Data (CPD/dai.cloud.ibm.com)
"""
import os
import logging
import warnings
from typing import List, Dict, Optional
from dotenv import load_dotenv

from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from agent_instructions import build_system_prompt

# Always reload .env so the client gets fresh values even after Flask reloader restarts
load_dotenv(override=True)

logger = logging.getLogger(__name__)

# Suppress harmless IBM SDK warnings in the console
warnings.filterwarnings("ignore", category=Warning, module="ibm_watsonx_ai")


def _build_credentials(api_key: str, url: str) -> Credentials:
    """
    Build Credentials object.
    - IBM Cloud (us-south.ml.cloud.ibm.com, etc.)  → api_key only
    - Cloud Pak for Data (*.dai.cloud.ibm.com)      → username + api_key + version
    """
    cpd_url = "dai.cloud.ibm.com" in url or "cp4d" in url
    if cpd_url:
        version  = os.environ.get("WATSONX_CPD_VERSION", "5.1")
        username = os.environ.get("WATSONX_USERNAME", "admin")
        logger.info("CPD URL detected — username=%s version=%s", username, version)
        return Credentials(api_key=api_key, url=url, username=username, version=version)
    return Credentials(api_key=api_key, url=url)


class WatsonxClient:
    """Wraps IBM watsonx.ai ModelInference for FitVerse chat completions."""

    def __init__(self, api_key: str, project_id: str, url: str, model_id: str):
        self.model_id   = model_id
        self.project_id = project_id
        credentials = _build_credentials(api_key, url)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
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
        """Send conversation history to the model and return the assistant reply."""
        system_prompt = build_system_prompt(user_profile)
        chat_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant"):
                chat_messages.append({"role": role, "content": content})

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
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
                logger.error("watsonx.ai chat error: %s", exc)
                # Fallback to generate_text
                try:
                    prompt = f"<|system|>\n{system_prompt}\n"
                    for msg in messages:
                        role    = msg.get("role", "user")
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
                        "I'm temporarily unavailable. Please try again in a moment."
                    )

    def generate_workout_plan(self, user_profile: Dict, goal: str, level: str, days: int) -> str:
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
        return self.chat(
            [{"role": "user", "content": "Give me one specific fitness tip for today based on my profile. Keep it under 100 words."}],
            user_profile=user_profile,
            max_tokens=150,
        )


# ── Singleton with auto-retry ─────────────────────────────────────────────────
_client_instance: Optional[WatsonxClient] = None


def _create_client() -> Optional[WatsonxClient]:
    """Read .env fresh and create a new WatsonxClient."""
    # Re-read .env every time so Flask reloader never uses stale values
    load_dotenv(override=True)

    api_key    = os.environ.get("WATSONX_API_KEY",    "").strip()
    project_id = os.environ.get("WATSONX_PROJECT_ID", "").strip()
    url        = os.environ.get("WATSONX_URL", "https://us-south.ml.cloud.ibm.com").rstrip("/")
    model_id   = os.environ.get("WATSONX_MODEL_ID",   "meta-llama/llama-3-3-70b-instruct").strip()

    if not api_key or not project_id:
        logger.warning("WATSONX_API_KEY or WATSONX_PROJECT_ID missing — AI offline.")
        return None

    if "your-ibm" in api_key or "dummy" in api_key or len(api_key) < 20:
        logger.warning("WATSONX_API_KEY looks like a placeholder — AI offline.")
        return None

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = WatsonxClient(api_key, project_id, url, model_id)
        logger.info("✅ watsonx.ai client ready — model: %s", model_id)
        return client
    except Exception as exc:
        logger.error("❌ watsonx.ai init failed: %s", exc)
        return None


def get_watsonx_client() -> Optional[WatsonxClient]:
    """
    Return a live WatsonxClient singleton.
    Re-reads .env and retries if the previous attempt failed,
    so Flask debug-mode reloads never leave AI permanently offline.
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = _create_client()
    return _client_instance


def reset_client():
    """Force re-initialisation on next call (used by app factory after .env reload)."""
    global _client_instance
    _client_instance = None
