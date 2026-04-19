from .tools.llm import generate_text

INTENT_DESCRIPTIONS = """
You are the intent router for DispatchIQ, an AI operations assistant for trucking fleets.
Your job is to read the dispatcher's message and map it strictly to one of the following operational intents:

Available intents:
- 'delivery_risk': Queries about drivers missing delivery windows or being late.
- 'active_alerts_summary': Queries asking about alerts, emergencies, or critical issues.
- 'fleet_summary': General queries about the fleet overview, overall counts, or simple fleet status.
- 'driver_status': Queries asking about a specific driver's current location, status, or HOS.
- 'available_drivers': Queries asking who is currently available for dispatch or resting.
- 'fuel_risk': Queries about drivers low on fuel.
- 'best_cost_per_mile': Queries about which driver is most cost effective.
- 'rank_drivers_for_load': Queries asking to rank or recommend drivers for a new or specific load/route.
- 'general_chat': Conversational questions, greetings, jokes, or general trucking discussion that doesn't fit operational intents.

Respond ONLY with the exact string name of the most appropriate intent from the list above. No quotes, no markdown, no other text.
"""

def fallback_detect_intent(question: str) -> str:
    """
    Very simple rule-based intent router for the hackathon (Fallback).
    Used if the LLM is offline or fails to classify.
    """
    question = question.lower()
    
    if "miss their delivery" in question or "delivery risk" in question:
        return "delivery_risk"
    elif "alert" in question or "critical" in question:
        return "active_alerts_summary"
    elif "status" in question:
         if "fleet" in question:
             return "fleet_summary"
         return "driver_status"
    elif "available for dispatch" in question or "how many drivers are available" in question:
        return "available_drivers"
    elif "low on fuel" in question or "fuel risk" in question:
        return "fuel_risk"
    elif "best cost per mile" in question or "lower cost" in question:
        return "best_cost_per_mile"
    elif "new load from" in question or "rank available drivers" in question:
        return "rank_drivers_for_load"
    elif "summary" in question:
        return "fleet_summary"
    elif question.strip() in ["hi", "hello", "hey"] or "hello" in question:
        return "greeting"
    
    return "unknown"


def detect_intent(question: str) -> str:
    """
    Dynamic LLM-based Intent NLU with legacy fallback.
    """
    # Fast paths for simple greetings
    quick_greetings = ["hi", "hello", "hey", "hi there", "sup"]
    if question.lower().strip() in quick_greetings:
        return "greeting"

    prompt = f"Analyze this dispatcher's message: '{question}'\n\nWhich intent does it map to?"

    try:
        response = generate_text(prompt, system_message=INTENT_DESCRIPTIONS)
        intent = response.strip().lower()
        
        valid_intents = [
            "delivery_risk", "active_alerts_summary", "fleet_summary", 
            "driver_status", "available_drivers", "fuel_risk", 
            "best_cost_per_mile", "rank_drivers_for_load", 
            "greeting", "general_chat", "unknown"
        ]
        
        if intent in valid_intents:
             return intent
        elif "mock response" in intent:
             # Fast fail into fallback if key isn't provided
             return fallback_detect_intent(question)
        else:
             # Try substring matching if LLM was verbose
             for v_intent in valid_intents:
                 if v_intent in intent:
                     return v_intent
             return "unknown"
    except Exception:
        return fallback_detect_intent(question)
