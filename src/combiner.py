import json
import os
import asyncio
from typing import List, Dict, Any
from src.agents.base import AgentResponse
from src.config import OrchestratorSettings

# Import SDKs for the Combiner (using OpenRouter/OpenAI for synthesis)
try:
    from openai import AsyncOpenAI
except ImportError:
    pass

class Combiner:
    def __init__(self, settings: OrchestratorSettings):
        self.settings = settings
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.client = None
        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1"
            )

    async def synthesize(self, user_query: str, responses: List[AgentResponse], critiques: List[str]) -> Dict[str, Any]:
        """
        Uses an LLM to aggregate all agent responses into a final, comprehensive answer.
        """
        # 1. Filter valid responses
        valid_responses = [r for r in responses if r.confidence > 0]
        
        if not valid_responses:
            return {
                "final_answer": "All agents failed to respond.",
                "combined_confidence": 0.0,
                "disagreement": "N/A",
                "recommended_next_steps": "Check system health.",
                "agents": []
            }

        # 2. Prepare Context for the Synthesizer
        agents_text = ""
        for r in valid_responses:
            agents_text += f"\n--- Agent: {r.name} (Confidence: {r.confidence}) ---\n{r.answer}\nRationale: {r.rationale}\n"
        
        critiques_text = "\n".join(critiques)

        # 3. Construct Prompt for Synthesis
        synthesis_prompt = f"""
        You are the Chief Editor of an AI expert panel.
        
        User Query: "{user_query}"
        
        Here are the draft answers from your team of specialists:
        {agents_text}
        
        Here are their cross-critiques:
        {critiques_text}
        
        Your Task:
        1. Synthesize a single, highly detailed, and comprehensive Final Answer (minimum 400 words).
        2. Merge the best insights from all agents.
        3. Resolve minor disagreements; note major ones.
        4. Maintain a professional, user-facing tone.
        
        Output Format (Strict JSON):
        {{
            "final_answer": "The detailed synthesized text...",
            "combined_confidence": 0.0 to 1.0 (average of input confidence),
            "disagreement": "Summary of any conflicts...",
            "recommended_next_steps": "Follow-up actions..."
        }}
        """

        # 4. Call LLM for Synthesis
        if self.client:
            try:
                response = await self.client.chat.completions.create(
                    model="openai/gpt-4o-mini", # Use a smart model for synthesis
                    messages=[{"role": "user", "content": synthesis_prompt}],
                    temperature=0.5
                )
                raw_content = response.choices[0].message.content
                clean_json = raw_content.replace("```json", "").replace("```", "").strip()
                result = json.loads(clean_json)
                
                # Attach individual agent details for the UI
                result["agents"] = [r.model_dump() for r in responses]
                return result
                
            except Exception as e:
                print(f"Combiner LLM Failed: {e}")
                # Fallback to heuristic if LLM fails
                return self._heuristic_fallback(valid_responses)
        else:
             return self._heuristic_fallback(valid_responses)

    def _heuristic_fallback(self, valid_responses: List[AgentResponse]) -> Dict[str, Any]:
        # Sort by confidence
        sorted_responses = sorted(valid_responses, key=lambda x: x.confidence, reverse=True)
        top_response = sorted_responses[0]
        
        return {
            "final_answer": f"[Fallback Synthesis] {top_response.answer}",
            "combined_confidence": top_response.confidence,
            "disagreement": "Synthesis LLM unavailable.",
            "recommended_next_steps": "Check API keys.",
            "agents": [r.model_dump() for r in valid_responses]
        }
