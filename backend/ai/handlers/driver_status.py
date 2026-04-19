from ..providers.base import FleetDataProvider
from ..schemas import AIResponse
from ..tools.llm import generate_text

def handle_driver_status(question: str, provider: FleetDataProvider, context: dict = None) -> AIResponse:
    drivers = provider.get_all_drivers()
    history = context.get("history") if context else None

    prompt = (
        f"User asked: '{question}'. \n"
        f"FACTS (List of all drivers and their details): {drivers}\n\n"
        "INSTRUCTION: Use the conversation history to determine which driver the user is asking about. "
        "Explain that specific driver's status, ETA, and details clearly. "
        "IMPORTANT: Only use the data provided above. If you cannot find the driver or the specific detail (like phone number), "
        "honestly state that the information is not available in the current database record."
    )
    
    answer = generate_text(prompt, history=history)
    return AIResponse("driver_status", answer, {})
