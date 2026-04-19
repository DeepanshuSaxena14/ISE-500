from ..providers.base import FleetDataProvider
from ..schemas import AIResponse
from ..tools.llm import generate_text

def handle_alerts(question: str, provider: FleetDataProvider, context: dict = None) -> AIResponse:
    alerts = provider.get_active_alerts()
    history = context.get("history") if context else None
    
    if not alerts:
        answer = generate_text(f"User asked: '{question}'. Fact: No active alerts. Reply accordingly.", history=history)
        return AIResponse("active_alerts_summary", answer, {"alerts": []})
    
    critical_count = len([a for a in alerts if a.get("severity") == "critical"])
    messages = [a.get("message", "") for a in alerts]
    
    prompt = f"User asked: '{question}'. Fact: {critical_count} critical alerts. Details: {messages}. Summarize clearly as DispatchIQ."
    answer = generate_text(prompt, history=history)
    
    return AIResponse("active_alerts_summary", answer, {"alerts": alerts}, ["What's James Okafor's current status?"])
