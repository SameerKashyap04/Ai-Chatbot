import asyncio
from src.config import load_config
from src.agents.simulated import SimulatedAgent

async def test_agent_simulation():
    print("--- Starting Agent Simulation Test ---")
    
    # Load config to get agent definitions
    config = load_config("orchestrator_config.yaml")
    
    user_query = "Why is the sky blue?"
    print(f"User Query: {user_query}\n")

    # Instantiate simulated agents
    agents = []
    for agent_cfg in config.agents:
        agent = SimulatedAgent(
            name=agent_cfg.name,
            vendor=agent_cfg.vendor,
            template=agent_cfg.template
        )
        agents.append(agent)

    # Test Query (Simulate Broadcast)
    print("Broadcasting query to agents...")
    tasks = [agent.query(user_query) for agent in agents]
    responses = await asyncio.gather(*tasks)

    for resp in responses:
        print(f"\n[Agent: {resp.name}]")
        print(f"  Confidence: {resp.confidence}")
        print(f"  Answer: {resp.answer[:100]}...") # Truncate for readability
        print(f"  Rationale: {resp.rationale}")

    print("\n--- Simulation Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test_agent_simulation())

