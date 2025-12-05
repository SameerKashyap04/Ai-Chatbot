import asyncio
from src.config import load_config
from src.orchestrator import MultiAgentOrchestrator

async def run_final_test():
    print("--- Day 7 Test: Safety & Polish ---")
    
    config = load_config("orchestrator_config.yaml")
    orchestrator = MultiAgentOrchestrator(config)
    
    # Test PII Redaction
    dangerous_query = "My email is test@example.com and phone is 555-123-4567. How do I fix my router?"
    print(f"\nUser Query (with PII): {dangerous_query}")
    
    # We expect the log to show "PII Redacted" and the agents to receive the cleaned version
    result = await orchestrator.process_query(dangerous_query)
    
    print("\n--- Final Answer ---")
    print(result['final_answer'])
    
    # Verify logic flow
    print("\n--- Agents Used ---")
    for a in result['agents']:
        print(f"- {a['name']}")

if __name__ == "__main__":
    asyncio.run(run_final_test())

