from ..providers.base import FleetDataProvider
from ..schemas import AIResponse
from ..tools.llm import generate_text

def handle_available_drivers(question: str, provider: FleetDataProvider, context: dict = None) -> AIResponse:
    drivers = provider.get_available_drivers()
    count = len(drivers)
    names = ", ".join([d.get("name") for d in drivers])
    prompt = f"User asked: '{question}'. Fact: {count} available -> {names}. Formulate a nice dispatch message."
    history = context.get("history") if context else None
    answer = generate_text(prompt, history=history)
    return AIResponse("available_drivers", answer, {"drivers": drivers}, ["Rank available drivers for a load to LA"])

def handle_delivery_risk(question: str, provider: FleetDataProvider, context: dict = None) -> AIResponse:
    drivers = provider.get_delivery_risk_drivers()
    history = context.get("history") if context else None
    if not drivers:
        return AIResponse("delivery_risk", generate_text("Tell user no drivers flagged for risk.", history=history))
    
    names = ", ".join([d.get("name") for d in drivers])
    prompt = f"User asked: '{question}'. Fact: {len(drivers)} at risk of missing delivery: {names}. Summarize."
    return AIResponse("delivery_risk", generate_text(prompt, history=history), {"drivers": drivers})

def handle_fuel_risk(question: str, provider: FleetDataProvider, context: dict = None) -> AIResponse:
    drivers = provider.get_low_fuel_en_route_drivers()
    history = context.get("history") if context else None
    if not drivers:
        return AIResponse("fuel_risk", generate_text("Tell user no en route drivers low on fuel.", history=history))
    
    names = ", ".join([d.get("name") for d in drivers])
    prompt = f"User asked '{question}'. Fact: {len(drivers)} low fuel: {names}. Alert them."
    return AIResponse("fuel_risk", generate_text(prompt, history=history), {"drivers": drivers})

def handle_best_cost_per_mile(question: str, provider: FleetDataProvider, context: dict = None) -> AIResponse:
    driver = provider.get_best_cost_per_mile_driver()
    history = context.get("history") if context else None
    if not driver:
        return AIResponse("best_cost_per_mile", generate_text("Tell user no available drivers.", history=history))
    
    prompt = f"User asked '{question}'. Fact: {driver['name']} is best at ${driver['cost_per_mile']}/mi. Convey this."
    return AIResponse("best_cost_per_mile", generate_text(prompt, history=history), {"driver": driver})

def handle_rank_drivers(question: str, provider: FleetDataProvider, context: dict = None) -> AIResponse:
    origin, destination = "Phoenix", "El Paso"
    if "tucson" in question.lower() and "la" in question.lower():
        origin, destination = "Tucson", "LA"
    drivers = provider.rank_drivers_for_load(origin, destination)
    history = context.get("history") if context else None
    if not drivers:
        return AIResponse("rank_drivers_for_load", generate_text("No drivers can be ranked.", history=history))
    
    top_driver = drivers[0]
    prompt = f"User asked: '{question}'. Fact: Best is {top_driver['name']} based on stats. Recommend them naturally."
    return AIResponse("rank_drivers_for_load", generate_text(prompt, history=history), {"ranked_drivers": drivers})
