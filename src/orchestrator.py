import asyncio
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from src.config import AppConfig, AgentConfig
from src.agents.base import BaseAgent, AgentResponse
from src.agents.simulated import SimulatedAgent
from src.agents.real import RealAgent
from src.combiner import Combiner
from src.sanitizer import Sanitizer

load_dotenv()

class MultiAgentOrchestrator:
    def __init__(self, config: AppConfig, use_real_agents: bool = False):
        self.config = config
        self.use_real_agents = use_real_agents
        self.agents: List[BaseAgent] = self._initialize_agents(config.agents)
        self.combiner = Combiner(config.orchestrator)
        self.sanitizer = Sanitizer(config.sanitization)
        print(f"Initialized {self.config.orchestrator.name} (Mode: {'REAL' if use_real_agents else 'SIMULATED'})")

    def _initialize_agents(self, agent_configs: List[AgentConfig]) -> List[BaseAgent]:
        agents = []
        for agent_cfg in agent_configs:
            if self.use_real_agents:
                agents.append(RealAgent(
                    name=agent_cfg.name,
                    vendor=agent_cfg.vendor,
                    template=agent_cfg.template
                ))
            else:
                agents.append(SimulatedAgent(
                    name=agent_cfg.name,
                    vendor=agent_cfg.vendor,
                    template=agent_cfg.template
                ))
        return agents

    async def broadcast_query(self, user_query: str) -> List[AgentResponse]:
        timeout_seconds = self.config.timeouts.initial_answer_seconds
        tasks = [agent.query(user_query) for agent in self.agents]
        
        print(f"Broadcasting to {len(self.agents)} agents...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_responses = []
        for i, result in enumerate(results):
            agent_name = self.agents[i].name
            if isinstance(result, Exception):
                print(f"xx Agent {agent_name} failed: {result}")
                valid_responses.append(AgentResponse(
                    name=agent_name,
                    answer="[Timeout/Error]",
                    rationale="Agent failed.",
                    confidence=0.0,
                    sources=[]
                ))
            else:
                valid_responses.append(result)
        return valid_responses

    async def run_critique_round(self, responses: List[AgentResponse]) -> List[str]:
        responses_data = [r.model_dump() for r in responses if r.confidence > 0]
        tasks = []
        for agent in self.agents:
            tasks.append(agent.critique(responses_data))
            
        print("Running critique round...")
        critiques = await asyncio.gather(*tasks, return_exceptions=True)
        
        clean_critiques = []
        for c in critiques:
            if isinstance(c, Exception):
                clean_critiques.append("Critique failed.")
            else:
                clean_critiques.append(c)
        return clean_critiques

    def validate_and_sanitize(self, user_query: str) -> str:
        """
        Step 1: Sanitize Input (PII Removal)
        """
        return self.sanitizer.sanitize(user_query)

    async def process_query(self, user_query: str) -> Dict[str, Any]:
        # 0. Sanitize
        clean_query = self.validate_and_sanitize(user_query)
        
        # 1. Broadcast
        responses = await self.broadcast_query(clean_query)
        
        # 2. Critique
        critiques = await self.run_critique_round(responses)
        
        # 3. Synthesize
        print("Synthesizing final answer...")
        # Pass user_query to synthesize
        final_result = await self.combiner.synthesize(user_query, responses, critiques)
        
        return final_result
