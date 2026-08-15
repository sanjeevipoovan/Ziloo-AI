"""
Context Builder.

Every code path that talks to a model - direct chat, an agent run, RAG -
goes through this one class to assemble the system prompt and message
list. That centralization is the "better prompting" half of this build:
no route or service hand-rolls a system prompt string or bolts RAG context
onto a message via ad hoc concatenation. Instructions are explicit
(what the context is for, how to cite it, what to do when it doesn't
answer the question) instead of assumed.
"""
from dataclasses import dataclass

from app.db.models.agent import Agent
from app.providers.base import ProviderMessage

DEFAULT_SYSTEM_PROMPT = (
    "You are MyAI, a helpful, honest AI assistant. Answer clearly and "
    "concisely. If you are not sure about something, say so rather than "
    "guessing."
)

_RAG_INSTRUCTIONS = (
    "Use the following retrieved context to answer the user's question when "
    "it is relevant. Cite sources inline by their bracketed number, e.g. "
    "[1]. If the context does not contain the answer, say so explicitly "
    "instead of guessing."
)


@dataclass
class AssembledContext:
    messages: list[ProviderMessage]
    system_prompt: str


class ContextBuilder:
    def build(
        self,
        *,
        user_input: str,
        agent: Agent | None = None,
        retrieved_chunks: list[str] | None = None,
        override_system_prompt: str | None = None,
    ) -> AssembledContext:
        system_prompt = override_system_prompt or (agent.system_prompt if agent else DEFAULT_SYSTEM_PROMPT)

        if retrieved_chunks:
            context_block = "\n\n".join(f"[{i + 1}] {chunk}" for i, chunk in enumerate(retrieved_chunks))
            system_prompt = f"{system_prompt}\n\n{_RAG_INSTRUCTIONS}\n\n--- Retrieved context ---\n{context_block}\n--- End context ---"

        return AssembledContext(
            messages=[ProviderMessage(role="system", content=system_prompt)],
            system_prompt=system_prompt,
        )
