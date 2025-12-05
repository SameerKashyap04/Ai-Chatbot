import asyncio
import json
import random
from typing import List, Optional, Dict, Any
from src.agents.base import BaseAgent, AgentResponse

class SimulatedAgent(BaseAgent):
    """
    A simulated agent that returns mock data based on its persona.
    Useful for testing the orchestration flow without incurring API costs.
    """

    async def query(self, user_query: str, history: Optional[List[Dict[str, str]]] = None) -> AgentResponse:
        # Simulate network latency
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # Mock logic to generate a "persona-based" answer
        # In a real scenario, this would call the LLM API with self.template + user_query
        
        if "ChatGPT" in self.name:
            answer = f"To answer '{user_query}', I would break this down into three key parts: context, mechanism, and implications. Here is a pragmatic explanation..."
            rationale = "I focused on structure and clarity as requested."
            confidence = 0.95
            sources = ["none"]
        elif "Claude" in self.name:
            answer = f"In summary, regarding '{user_query}': The key safety considerations are X and Y. Code is concise."
            rationale = "Prioritized safety and summarization."
            confidence = 0.9
            sources = ["Anthropic docs"]
        elif "Gemini" in self.name:
            answer = f"Here is the latest info on '{user_query}' based on my retrieval capabilities. [Image placeholder]"
            rationale = "Used multimodal retrieval context."
            confidence = 0.85
            sources = ["Google Search", "YouTube"]
        elif "Grok" in self.name:
            answer = f"Let's be real about '{user_query}'. It's mostly XYZ. Here's the raw truth."
            rationale = "Adopted a speculative, unfiltered stance."
            confidence = 0.7
            sources = ["X (Twitter)"]
        else:
            answer = f"[{self.name}] Answer to: {user_query}"
            rationale = f"Standard {self.name} logic."
            confidence = 0.8
            sources = ["Internal DB"]

        return AgentResponse(
            name=self.name,
            answer=answer,
            rationale=rationale,
            confidence=confidence,
            sources=sources
        )

    async def critique(self, other_responses: List[Dict[str, Any]]) -> str:
        await asyncio.sleep(0.2)
        return f"{self.name} thinks the other answers are generally okay, but could be more specific."

