import os
import json
import asyncio
from typing import List, Optional, Dict, Any
from src.agents.base import BaseAgent, AgentResponse

# Import SDKs
try:
    from openai import AsyncOpenAI
except ImportError:
    print("Warning: openai SDK not installed.")

try:
    import google.generativeai as genai
except ImportError:
    print("Warning: google-generativeai SDK not installed.")

class RealAgent(BaseAgent):
    """
    A real agent implementation that supports:
    1. Google Gemini via Native Google SDK (if vendor="Google")
    2. All other models via OpenRouter (OpenAI-compatible)
    """

    def __init__(self, name: str, vendor: str, template: str):
        super().__init__(name, vendor, template)
        self.client = None
        self.is_native_google = False
        
        if vendor == "Google":
            self.api_key = os.getenv("GOOGLE_API_KEY")
            if self.api_key and not self.api_key.startswith("sk-or-v1"):
                self.is_native_google = True
                self._setup_google_client()
            else:
                # Fallback to OpenRouter if the key looks like an OpenRouter key
                self.api_key = os.getenv("GOOGLE_OPENROUTER_KEY") or os.getenv("OPENROUTER_API_KEY")
                self._setup_openrouter_client()
        else:
            self.api_key = os.getenv("OPENROUTER_API_KEY")
            self._setup_openrouter_client()

    def _setup_google_client(self):
        try:
            genai.configure(api_key=self.api_key)
            # We don't store a persistent client object for genai, we use the module + model instantiation
            pass
        except Exception as e:
            print(f"Failed to setup Google Client: {e}")

    def _setup_openrouter_client(self):
        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1"
            )

    def _get_openrouter_model(self) -> str:
        """Maps the agent vendor/name to a specific OpenRouter model ID."""
        if "ChatGPT" in self.name: return "openai/gpt-4o-mini"
        elif "Claude" in self.name: return "anthropic/claude-3-haiku"
        elif "Copilot" in self.name: return "microsoft/wizardlm-2-8x22b"
        elif "Grok" in self.name: return "meta-llama/llama-3.1-70b-instruct"
        elif "Perplexity" in self.name: return "perplexity/llama-3-sonar-large-32k-online"
        elif "DeepSeek" in self.name: return "deepseek/deepseek-chat"
        elif "Character" in self.name: return "meta-llama/llama-3-70b-instruct"
        return "openai/gpt-3.5-turbo"

    async def query(self, user_query: str, history: Optional[List[Dict[str, str]]] = None) -> AgentResponse:
        
        # --- PATH 1: Native Google Gemini ---
        if self.is_native_google:
            return await self._query_google_native(user_query)
            
        # --- PATH 2: OpenRouter ---
        if self.client:
            return await self._query_openrouter(user_query)

        # --- Fallback ---
        return await self._simulate_response(user_query, missing_key=True)

    async def _query_google_native(self, user_query: str) -> AgentResponse:
        try:
            # Create model instance (Flash is safer availability-wise than Pro for some keys)
            model = genai.GenerativeModel("gemini-1.5-flash") 
            
            # Combine template + query because Gemini handles system prompts differently or via config
            # But simple concatenation works well for this use case
            full_prompt = f"System: {self.template}\n\nUser: {user_query}\n\nRespond in strict JSON."
            
            # Run in thread executor because google SDK is sync
            response = await asyncio.to_thread(model.generate_content, full_prompt)
            raw_content = response.text
            
            return self._parse_json_response(raw_content)

        except Exception as e:
            print(f"Error calling Native Google API: {e}")
            return AgentResponse(
                name=self.name,
                answer=f"Google API Error: {str(e)}",
                rationale="API Call Failed",
                confidence=0.0,
                sources=[]
            )

    async def _query_openrouter(self, user_query: str) -> AgentResponse:
        try:
            model_id = self._get_openrouter_model()
            response = await self.client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": self.template},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.7,
                extra_headers={"HTTP-Referer": "http://localhost:8501", "X-Title": "Multi-Agent Orchestrator"}
            )
            raw_content = response.choices[0].message.content
            return self._parse_json_response(raw_content)

        except Exception as e:
            print(f"Error calling OpenRouter for {self.name}: {e}")
            return AgentResponse(
                name=self.name,
                answer=f"Error: {str(e)}",
                rationale="API Call Failed",
                confidence=0.0,
                sources=[]
            )

    def _parse_json_response(self, raw_content: str) -> AgentResponse:
        try:
            clean_json = raw_content.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            # Normalize keys
            if "response" in data and "answer" not in data: data["answer"] = data["response"]
            if "reasoning" in data and "rationale" not in data: data["rationale"] = data["reasoning"]
            if "confidence" not in data: data["confidence"] = 0.5
            if "sources" not in data: data["sources"] = []
            
            return AgentResponse(**data, name=self.name)
        except (json.JSONDecodeError, Exception) as e:
            return AgentResponse(
                name=self.name,
                answer=raw_content,
                rationale="Model returned plain text.",
                confidence=0.7,
                sources=["Raw Output"]
            )

    async def critique(self, other_responses: List[Dict[str, Any]]) -> str:
        # Simple critique logic
        prompt = f"Briefly critique these answers (1 sentence max): {json.dumps(other_responses)}"
        
        if self.is_native_google:
            try:
                model = genai.GenerativeModel("gemini-1.5-pro")
                resp = await asyncio.to_thread(model.generate_content, prompt)
                return resp.text
            except:
                return "Critique failed."
        
        if self.client:
            try:
                model_id = self._get_openrouter_model()
                resp = await self.client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": prompt}]
                )
                return resp.choices[0].message.content
            except:
                return "Critique failed."
                
        return "Simulated Critique: Looks good."

    async def _simulate_response(self, user_query: str, missing_key: bool = False) -> AgentResponse:
        return AgentResponse(
            name=self.name,
            answer="[MISSING KEY] Please set API keys in .env",
            rationale="Key missing",
            confidence=0.0,
            sources=[]
        )
