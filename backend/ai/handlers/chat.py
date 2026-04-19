from typing import Any
from ..schemas import AIResponse
from ..tools.llm import generate_text

def handle_chat(question: str, provider: Any, context: dict = None) -> AIResponse:
    prompt = f"The user just said: '{question}'. Reply conversationally as DispatchIQ. If it's a general greeting, say hi and state you're ready to help manage their fleet. If it is a joke, laugh and reply. If it's general trucking talk, respond appropriately but keep it brief."
    
    history = context.get("history") if context else None
    answer = generate_text(prompt, history=history)
    
    return AIResponse(
        intent="general_chat",
        answer=answer,
        data={},
        suggested_followups=["Give me a summary of all active alerts", "How many drivers are available?"]
    )

