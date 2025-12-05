# Multi-Agent Orchestrator Chatbot

This project implements a Multi-Agent Orchestrator that coordinates specialized AI agents (ChatGPT, Claude, Gemini, etc.) to answer user queries.

## Configuration

The core logic is defined in `orchestrator_config.yaml`.

## Setup

1.  Install dependencies (TBD - e.g., `pip install -r requirements.txt`).
2.  Set up API keys (see `.env.example`).
3.  Run the application.

## Features

-   **Query Validation**: Ensures clarity before processing.
-   **Broadcast**: Sends queries to all agents in parallel.
-   **Critique Round**: Agents review each other's answers.
-   **Synthesis**: Combines answers based on confidence and consensus.

