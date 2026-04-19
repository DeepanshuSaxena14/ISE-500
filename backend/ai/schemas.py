from typing import List, Dict, Any

class AIResponse:
    def __init__(self, intent: str, answer: str, data: Dict[str, Any] = None, suggested_followups: List[str] = None):
        self.intent = intent
        self.answer = answer
        self.data = data or {}
        self.suggested_followups = suggested_followups or []

    def to_dict(self):
        return {
            "intent": self.intent,
            "answer": self.answer,
            "data": self.data,
            "suggested_followups": self.suggested_followups
        }
