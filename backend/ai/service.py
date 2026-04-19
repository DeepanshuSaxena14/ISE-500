from typing import Dict, Any

from .intents import detect_intent
from .providers.mock_provider import MockFleetProvider
from .providers.api_provider import APIFleetProvider

from .handlers.fleet_summary import handle_fleet_summary
from .handlers.alerts import handle_alerts
from .handlers.driver_status import handle_driver_status
from .handlers.chat import handle_chat
from .handlers.dispatch import (
    handle_available_drivers,
    handle_delivery_risk,
    handle_fuel_risk,
    handle_best_cost_per_mile,
    handle_rank_drivers
)

# For hackathon/demo, we use Mock provider by default.
provider = MockFleetProvider()

def process_dispatch_query(question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Main entry point for AI layer queries.
    """
    intent = detect_intent(question)
    
    if intent == "fleet_summary":
        response = handle_fleet_summary(question, provider, context)
    elif intent in ["greeting", "general_chat"]:
        response = handle_chat(question, provider, context)
    elif intent == "active_alerts_summary":
        response = handle_alerts(question, provider, context)
    elif intent == "driver_status":
        response = handle_driver_status(question, provider, context)
    elif intent == "available_drivers":
        response = handle_available_drivers(question, provider, context)
    elif intent == "delivery_risk":
        response = handle_delivery_risk(question, provider, context)
    elif intent == "fuel_risk":
        response = handle_fuel_risk(question, provider, context)
    elif intent == "best_cost_per_mile":
        response = handle_best_cost_per_mile(question, provider, context)
    elif intent == "rank_drivers_for_load":
        response = handle_rank_drivers(question, provider, context)
    else:
        response = handle_fleet_summary(question, provider, context)
        response.intent = "unknown"
        response.answer = "I couldn't quite understand. Here is the fleet summary instead: " + response.answer

    return response.to_dict()
