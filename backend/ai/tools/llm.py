from ..config import config

try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage
except ImportError:
    ChatGroq = None

def generate_text(prompt: str, system_message: str = "You are DispatchIQ, a helpful fleet assistant.", history: list = None) -> str:
    """
    Generate text using Groq and LangChain with conversational memory.
    """
    if not ChatGroq or config.GROQ_API_KEY == "dummy_groq_key":
        return "I am a mock response. Please provide a valid GROQ_API_KEY."
    
    chat = ChatGroq(temperature=0, api_key=config.GROQ_API_KEY, model_name=config.GROQ_MODEL)
    messages = [SystemMessage(content=system_message)]
    
    if history:
        from langchain_core.messages import AIMessage
        for msg in history[:-1]:  # Exclude the latest user message which is sent as prompt
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant" or role == "ai":
                messages.append(AIMessage(content=content))
                
    messages.append(HumanMessage(content=prompt))
    response = chat.invoke(messages)
    return response.content
