import sys
from src.config import load_config
from src.orchestrator import MultiAgentOrchestrator

def main():
    try:
        # Load configuration
        print("Loading configuration...")
        config = load_config("orchestrator_config.yaml")
        
        # Initialize Orchestrator
        orchestrator = MultiAgentOrchestrator(config)
        
        # Print Status to verify
        orchestrator.print_status()
        
        print("Day 1: Foundation setup complete. Config loaded successfully.")
        
    except Exception as e:
        print(f"Error initializing application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

