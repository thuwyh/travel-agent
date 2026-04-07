"""
LLM client wrapper with token usage and cost tracking.
"""

import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
DEFAULT_MODEL = "openai/gpt-oss-20b"

# Pricing per 1M tokens
INPUT_PRICE = 0.075
CACHED_PRICE = 0.037
OUTPUT_PRICE = 0.30


class SessionUsage(BaseModel):
    """Tracks cumulative token usage and cost across an agent session."""

    total_prompt_tokens: int = 0
    total_cached_tokens: int = 0
    total_completion_tokens: int = 0
    total_cost: float = 0.0
    steps: List[Dict[str, Any]] = Field(default_factory=list)

    def record(self, prompt: int, cached: int, completion: int, label: str = "") -> None:
        uncached = prompt - cached
        cost = (uncached * INPUT_PRICE + cached * CACHED_PRICE + completion * OUTPUT_PRICE) / 1_000_000
        self.total_prompt_tokens += prompt
        self.total_cached_tokens += cached
        self.total_completion_tokens += completion
        self.total_cost += cost
        step = {
            "step": len(self.steps) + 1,
            "label": label,
            "prompt": prompt,
            "cached": cached,
            "completion": completion,
            "cost": cost,
        }
        self.steps.append(step)
        print(
            f"  [tokens] {label or f'step={step['step']}'}"
            f"  prompt={prompt} (cached={cached})"
            f"  completion={completion}"
            f"  cost=${cost:.6f}"
            f"  total=${self.total_cost:.6f}"
        )

    def summary(self) -> str:
        return (
            f"SESSION TOTAL: prompt={self.total_prompt_tokens}"
            f" (cached={self.total_cached_tokens})"
            f"  completion={self.total_completion_tokens}"
            f"  cost=${self.total_cost:.6f}"
        )


async def chat_completion(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict]] = None,
    usage: Optional[SessionUsage] = None,
    model: str = DEFAULT_MODEL,
    label: str = "",
    parallel_tool_calls: bool = False,
):
    """
    Thin wrapper around the chat completions API.
    Tracks token usage into the SessionUsage if provided.
    Returns the raw API response.
    """
    kwargs: Dict[str, Any] = {"model": model, "messages": messages}
    if tools:
        kwargs["tools"] = tools
        if parallel_tool_calls:
            kwargs["parallel_tool_calls"] = True

    response = await client.chat.completions.create(**kwargs)

    if usage and response.usage:
        p = response.usage.prompt_tokens
        c = response.usage.completion_tokens
        details = getattr(response.usage, "prompt_tokens_details", None)
        cached = (details.cached_tokens or 0) if details and hasattr(details, "cached_tokens") else 0
        usage.record(prompt=p, cached=cached, completion=c, label=label)

    return response
