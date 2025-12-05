import yaml
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class OrchestratorSettings(BaseModel):
    name: str
    description: str
    system_prompt: str
    combiner_rules: str
    output_requirements: str

class OutputSchema(BaseModel):
    orchestration_result: Dict[str, Any]

class AgentConfig(BaseModel):
    name: str
    vendor: str
    template: str

class DiscussionConfig(BaseModel):
    rules: str

class TimeoutsConfig(BaseModel):
    initial_answer_seconds: int
    discussion_answer_seconds: int
    total_orchestration_seconds: int

class SanitizationConfig(BaseModel):
    redact_user_pii: bool
    pii_rules: str

class ExampleConfig(BaseModel):
    user_query: str
    sample_orchestration_result: str

class AppConfig(BaseModel):
    orchestrator: OrchestratorSettings
    output_schema: OutputSchema
    agents: List[AgentConfig]
    cross_agent_discussion: DiscussionConfig
    timeouts: TimeoutsConfig
    sanitization: SanitizationConfig
    implementation_tips: str
    example: ExampleConfig

def load_config(config_path: str = "orchestrator_config.yaml") -> AppConfig:
    """Loads and validates the YAML configuration."""
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)
    
    return AppConfig(**raw_config)

