from ..providers.base import FleetDataProvider
from ..schemas import AIResponse
from ..tools.llm import generate_text

def handle_driver_status(question: str, provider: FleetDataProvider, context: dict = None) -> AIResponse:
    drivers = provider.get_all_drivers()
    history = context.get("history") if context else None

    prompt = f"User asked: '{question}'. Facts for all drivers: {drivers}. Use the conversation history to determine which driver the user is asking about (if they used vague words like 'he' or 'his'). Explain that specific driver's status, ETA, and fuel level clearly."
    
    answer = generate_text(prompt, history=history)
    return AIResponse("driver_status", answer, {})
