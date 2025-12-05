# 7-Day Implementation Plan: Multi-Agent Orchestrator

This plan breaks down the development of the Multi-Agent Orchestrator into manageable daily milestones, focusing on building a robust local demo.

## Day 1: Foundation & Configuration
**Goal:** Set up the project structure and load the orchestration configuration.
- [ ] Initialize Python environment (virtualenv/poetry).
- [ ] Install base dependencies (`pydantic`, `pyyaml`, `python-dotenv`).
- [ ] Implement `ConfigLoader` to parse `orchestrator_config.yaml`.
- [ ] Create the basic `Orchestrator` class shell.
- [ ] **Deliverable:** A script that loads the YAML config and prints the agent list and rules.

## Day 2: Agent Architecture & Simulation
**Goal:** Define the generic Agent interface and build "Simulated" versions for testing.
- [ ] Define the abstract `BaseAgent` class (methods: `query`, `critique`).
- [ ] Implement `SimulatedAgent` that returns mock data (based on the YAML templates) without calling real APIs.
- [ ] Implement the prompt template rendering system (injecting user query into agent-specific system prompts).
- [ ] **Deliverable:** A script where you can send a string to a "Simulated ChatGPT" and get a mock JSON response.

## Day 3: The Orchestration Loop (Part 1: Broadcast & Collect)
**Goal:** Implement the parallel broadcasting and response collection.
- [ ] Implement `async` logic to broadcast queries to all agents simultaneously.
- [ ] Handle timeouts (as defined in `orchestrator_config.yaml`).
- [ ] Implement response validation (ensure agents return valid JSON).
- [ ] **Deliverable:** The Orchestrator can take a query, fire it to 7 simulated agents, and collect 7 raw responses (or timeout errors) in a list.

## Day 4: The Orchestration Loop (Part 2: Critique & Synthesis)
**Goal:** Implement the cross-agent discussion and final combination logic.
- [ ] Implement the "Critique Round": Feed other agents' answers back to them for 1-sentence feedback.
- [ ] Implement `Combiner` logic:
    - Weight answers by confidence.
    - Detect disagreement (heuristic or LLM-based).
    - Synthesize the final answer.
- [ ] **Deliverable:** A complete console-based run: Query -> Agents Answer -> Agents Critique -> Final Result printed to terminal.

## Day 5: API Integration & "Real" Agents
**Goal:** Connect to actual LLM APIs (or a single powerful model roleplaying them).
- [ ] Create `RealAgent` implementations for OpenAI, Anthropic, Google, etc.
- [ ] *Alternative:* Implement a `RoleplayAgent` that uses GPT-4 or Claude 3.5 to *simulate* the specific personas of other models if you don't have all API keys.
- [ ] Add PII redaction/sanitization middleware.
- [ ] **Deliverable:** The system now generates real, dynamic intelligence instead of static mocks.

## Day 6: Visualization & UI
**Goal:** Build a frontend to visualize the multi-agent process.
- [ ] Set up a Streamlit or Gradio app.
- [ ] Create a chat interface for the user.
- [ ] Add an "Under the Hood" expander to show:
    - Individual Agent Answers.
    - Confidence Scores.
    - The Critique/Discussion log.
- [ ] **Deliverable:** A browser-based UI where you can chat with the Orchestrator.

## Day 7: Polish, Safety & Demo Prep
**Goal:** Refine the experience for the final demo.
- [ ] Implement the "Clarifying Question" logic (Step 1 of system prompt).
- [ ] Fine-tune the system prompts to ensure consistent JSON output.
- [ ] Add logging for the "audit" requirement.
- [ ] Test with edge cases (ambiguous queries, dangerous queries).
- [ ] **Deliverable:** Final polished Multi-Agent Chatbot ready for presentation.

