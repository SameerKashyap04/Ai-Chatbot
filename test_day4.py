import asyncio
import json
from src.config import load_config
from src.orchestrator import MultiAgentOrchestrator

async def run_full_flow():
    print("--- Day 4 Test: Full Orchestration Flow ---")
    
    config = load_config("orchestrator_config.yaml")
    orchestrator = MultiAgentOrchestrator(config)
    
    user_query = "How does photosynthesis work?"
    print(f"\nUser Query: {user_query}\n")
    
    result = await orchestrator.process_query(user_query)
    
    print("\n--- Final Orchestration Result ---")
    print(json.dumps(result, indent=2))
    
    print("\n--- Summary ---")
    print(f"Final Answer: {result['final_answer'][:100]}...")
    print(f"Confidence: {result['combined_confidence']}")
    print(f"Disagreement: {result['disagreement']}")

if __name__ == "__main__":
    asyncio.run(run_full_flow())

