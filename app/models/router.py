"""
Model Router: a deterministic (non-ML) V1 routing policy.

Deliberately simple, as specified: short/simple requests go to GLM-5.2,
long-context/complex/reasoning-flavored requests go to Kimi K3. This is a
standalone component (not embedded in a route handler) specifically so a
future version can swap `_decide_auto` for a real complexity classifier,
or extend it to weigh latency/cost/availability, without touching any
caller.
"""
from dataclasses import dataclass

from app.core.exceptions import ValidationAppError
from app.db.models.model import AIModel
from app.models.registry import ModelRegistry

GLM_NAME = "glm-5.2"
KIMI_NAME = "kimi-k3"
AUTO = "auto"

# Requests whose combined text is at least this long are treated as
# "long-context" and routed to Kimi K3.
_LONG_CONTEXT_CHAR_THRESHOLD = 6000

# Presence of any of these (case-insensitive) is treated as a signal of
# complex reasoning / debugging / multi-step planning.
_COMPLEX_KEYWORDS = (
    "debug",
    "step by step",
    "step-by-step",
    "architecture",
    "refactor",
    "prove that",
    "algorithm",
    "optimi",  # optimise / optimize
    "trace through",
    "root cause",
    "multi-step",
    "multi step",
    "reasoning",
)

# A message containing several sizeable code fences is treated as complex coding.
_CODE_FENCE_COMPLEXITY_THRESHOLD = 4


@dataclass
class RoutingDecision:
    model: AIModel
    reason: str


class ModelRouter:
    def __init__(self, registry: ModelRegistry):
        self._registry = registry

    async def resolve(self, requested_model: str, message_contents: list[str]) -> RoutingDecision:
        if requested_model == AUTO:
            target_name = self._decide_auto(message_contents)
            model = await self._registry.get_by_name(target_name)
            if not model:
                raise ValidationAppError(f"No active model registered for '{target_name}'")
            return RoutingDecision(model=model, reason=f"auto-routed to {target_name}")

        model = await self._registry.get_by_name(requested_model)
        if not model:
            raise ValidationAppError(f"Unknown or inactive model '{requested_model}'")
        return RoutingDecision(model=model, reason="explicit selection")

    def _decide_auto(self, message_contents: list[str]) -> str:
        combined = "\n".join(message_contents)
        lowered = combined.lower()

        if len(combined) >= _LONG_CONTEXT_CHAR_THRESHOLD:
            return KIMI_NAME

        if any(keyword in lowered for keyword in _COMPLEX_KEYWORDS):
            return KIMI_NAME

        if combined.count("```") >= _CODE_FENCE_COMPLEXITY_THRESHOLD:
            return KIMI_NAME

        return GLM_NAME
