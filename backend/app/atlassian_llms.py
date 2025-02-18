import os
from enum import Enum
from langchain_openai import ChatOpenAI

class AtlassianModelProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"

HEADERS = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Atlassian-CloudId": "autofix-test",
        "X-Atlassian-UseCaseId": "autofix-service-evaluation",
        "X-Atlassian-UserId": os.environ.get("ATLASSIAN_USER_ID"),
        "Lanyard-Config": os.environ.get("ATLASSIAN_LANYARD_CONFIG_KEY"),
    }


def get_atlassian_llm(model: str, model_provider: AtlassianModelProvider):
    if model_provider == AtlassianModelProvider.OPENAI:
        reasoning_model = 'o3' in model or 'o1' in model
        return ChatOpenAI(
            model=model,
            base_url="http://host.docker.internal:3496/ai-gateway.us-east-1.staging.atl-paas.net/v1/openai/v1",
            default_headers=HEADERS,
            api_key=os.environ.get("ATLASSIAN_LANYARD_CONFIG_KEY"),
            temperature=None if reasoning_model else 0.0
        )
