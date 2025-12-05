import asyncio
import os
from src.config import load_config
from src.orchestrator import MultiAgentOrchestrator

async def run_real_test():
    print("--- Day 5 Test: Real Agent Integration ---")
    
    # Simulate an environment variable for testing "Real" mode logic
    os.environ["OPENAI_API_KEY"] = "sk-fake-key-for-testing"
    
    config = load_config("orchestrator_config.yaml")
    
    # Initialize with use_real_agents=True
    orchestrator = MultiAgentOrchestrator(config, use_real_agents=True)
    
    user_query = "What is the future of AI?"
    print(f"\nUser Query: {user_query}\n")
    
    result = await orchestrator.process_query(user_query)
    
    print("\n--- Result Snippet ---")
    # Show the first agent's response to verify it hit the RealAgent class
    if result['agents']:
        print(f"Agent 0 ({result['agents'][0]['name']}) Answer: {result['agents'][0]['answer']}")

if __name__ == "__main__":
    asyncio.run(run_real_test())

