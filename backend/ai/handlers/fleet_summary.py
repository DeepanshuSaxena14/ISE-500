from ..providers.base import FleetDataProvider
from ..schemas import AIResponse
from ..tools.llm import generate_text

def handle_fleet_summary(question: str, provider: FleetDataProvider, context: dict = None) -> AIResponse:
    data = provider.get_fleet_summary()
    
    prompt = f"The user asked: '{question}'. Fact: You have {data.get('total_drivers', 0)} total drivers. {data.get('en_route', 0)} en route, {data.get('available', 0)} available. {data.get('active_alerts', 0)} active alerts. Reply natively as DispatchIQ summarizing this to the user."
    history = context.get("history") if context else None
    answer = generate_text(prompt, history=history)
    
    return AIResponse(
        intent="fleet_summary",
        answer=answer,
        data=data,
        suggested_followups=["Give me a summary of all active alerts", "How many drivers are available for dispatch?"]
    )
