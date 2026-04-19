from ..providers.base import FleetDataProvider
from ..schemas import AIResponse
from ..tools.llm import generate_text

def handle_fleet_summary(question: str, provider: FleetDataProvider, context: dict = None) -> AIResponse:
    data = provider.get_fleet_summary()
    drivers = provider.get_all_drivers()
    
    # Extract names for the prompt so the AI doesn't hallucinate them
    driver_names = [d.get("name") for d in drivers if d.get("name")]
    
    prompt = (
        f"The user asked: '{question}'. \n"
        f"FACTS FROM DATABASE:\n"
        f"- Total Drivers: {data.get('total_drivers', 0)}\n"
        f"- En Route: {data.get('en_route', 0)}\n"
        f"- Available: {data.get('available', 0)}\n"
        f"- Active Alerts: {data.get('active_alerts', 0)}\n"
        f"- Actual Driver Names in Fleet: {', '.join(driver_names) if driver_names else 'None found'}\n\n"
        "INSTRUCTION: Summarize the fleet status. If asked for names, ONLY use the names provided above. "
        "If no names are provided, state that the fleet list is currently empty."
    )
    history = context.get("history") if context else None
    answer = generate_text(prompt, history=history)
    
    return AIResponse(
        intent="fleet_summary",
        answer=answer,
        data=data,
        suggested_followups=["Give me a summary of all active alerts", "How many drivers are available for dispatch?"]
    )
