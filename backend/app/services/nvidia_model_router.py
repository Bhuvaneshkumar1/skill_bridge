import logging
import os
from typing import Dict, Any, List, Optional
from openai import OpenAI
from backend.app.config import settings

logger = logging.getLogger(__name__)

# Active NVIDIA NIM Model Catalog Pools
NVIDIA_MODEL_POOLS: Dict[str, List[str]] = {
    "orchestration": [
        "nvidia/llama-3.1-nemotron-70b-instruct",
        "nvidia/llama-3.1-nemotron-51b-instruct",
        "mistralai/mistral-large-2-instruct",
        "meta/llama-3.2-90b-vision-instruct"
    ],
    "reasoning": [
        "deepseek-ai/deepseek-v4.1-flash",
        "nvidia/llama-3.1-nemotron-70b-instruct",
        "mistralai/mistral-large-2-instruct"
    ],
    "evaluation": [
        "microsoft/phi-3.5-moe-instruct",
        "mistralai/mistral-7b-instruct-v0.3",
        "nvidia/llama-3.1-nemotron-51b-instruct"
    ]
}

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

class NVIDIAModelRouter:
    """
    NVIDIA NIM Multi-Model Router & Automatic Model Fallback Engine.
    Routes tasks to specialized AI models and automatically switches to alternative
    models from the NVIDIA NIM catalog when one model is exhausted or rate-limited.
    """

    _client: Optional[OpenAI] = None

    @classmethod
    def get_client(cls) -> Optional[OpenAI]:
        api_key = settings.NVIDIA_API_KEY or os.getenv("NVIDIA_API_KEY", "")
        if not api_key:
            return None

        if cls._client is None or getattr(cls._client, "api_key", None) != api_key:
            cls._client = OpenAI(
                base_url=NVIDIA_BASE_URL,
                api_key=api_key
            )
        return cls._client

    @classmethod
    def chat_completion_with_fallback(
        cls,
        task_type: str,  # 'orchestration', 'reasoning', or 'evaluation'
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = "auto",
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Executes a chat completion across model fallbacks.
        If the primary model fails or hits limits, automatically rotates to the next model.
        """
        client = cls.get_client()
        if not client:
            return {
                "success": False,
                "error": "No NVIDIA_API_KEY configured.",
                "completion": None,
                "model_used": None,
                "switched_models": []
            }
        candidate_models = NVIDIA_MODEL_POOLS.get(task_type, NVIDIA_MODEL_POOLS["orchestration"])
        switched_models = []
        last_exception = None

        for model_name in candidate_models:
            try:
                logger.info(f"[NVIDIA NIM Router] Attempting completion using model: {model_name}")

                kwargs: Dict[str, Any] = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "timeout": 8.0
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = tool_choice

                completion = client.chat.completions.create(**kwargs)

                return {
                    "success": True,
                    "completion": completion,
                    "model_used": model_name,
                    "switched_models": switched_models,
                    "task_type": task_type
                }
            except Exception as exc:
                err_msg = str(exc)
                logger.warning(f"[NVIDIA NIM Router] Model '{model_name}' failed ({err_msg}). Switching to next model...")
                switched_models.append({"model": model_name, "error": err_msg})
                last_exception = exc

                # If account is not authorized or function does not exist for this account, all models will fail.
                # Fast-fail to prevent delaying agent response by 30+ seconds.
                err_lower = err_msg.lower()
                if "not found for account" in err_lower or "404" in err_lower or "unauthorized" in err_lower or "401" in err_lower:
                    logger.info("[NVIDIA NIM Router] Account does not have NIM function access. Fast-failing to agent tutor.")
                    break

        # Return failure details if all models in pool failed
        return {
            "success": False,
            "error": f"All candidate models for task '{task_type}' exhausted. Last error: {str(last_exception)}",
            "switched_models": switched_models,
            "model_used": candidate_models[0]
        }
