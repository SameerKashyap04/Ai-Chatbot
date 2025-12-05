import asyncio
from src.config import load_config
from src.orchestrator import MultiAgentOrchestrator

async def run_orchestration_loop():
    print("--- Day 3 Test: Orchestration Loop (Broadcast) ---")
    
    # 1. Load Config
    config = load_config("orchestrator_config.yaml")
    
    # 2. Init Orchestrator
    orchestrator = MultiAgentOrchestrator(config)
    
    # 3. Define a query
    user_query = "What is the capital of France?"
    
    # 4. Run Broadcast
    print(f"\nUser Query: {user_query}")
    responses = await orchestrator.broadcast_query(user_query)
    
    # 5. Display Results
    print(f"\nCollected {len(responses)} responses:")
    for resp in responses:
        status_icon = "✅" if resp.confidence > 0 else "❌"
        print(f"{status_icon} {resp.name}: [{resp.confidence}] {resp.answer[:50]}...")

if __name__ == "__main__":
    asyncio.run(run_orchestration_loop())

