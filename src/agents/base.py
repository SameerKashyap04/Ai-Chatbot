from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class AgentResponse(BaseModel):
    name: str
    answer: str
    rationale: str
    confidence: float
    sources: List[str]

class BaseAgent(ABC):
    def __init__(self, name: str, vendor: str, template: str):
        self.name = name
        self.vendor = vendor
        self.template = template

    @abstractmethod
    async def query(self, user_query: str, history: Optional[List[Dict[str, str]]] = None) -> AgentResponse:
        """
        Broadcasts the user query to the agent and returns a structured response.
        """
        pass

    @abstractmethod
    async def critique(self, other_responses: List[Dict[str, Any]]) -> str:
        """
        Asks the agent to critique other agents' answers.
        Returns a short string or JSON snippet.
        """
        pass

