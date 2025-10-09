"""Pipeline state definition for LangGraph."""

from typing import Any, Dict, List, TypedDict


class PipelineState(TypedDict):
    """State schema for the analysis pipeline.

    This TypedDict defines the structure of state that flows through
    the LangGraph pipeline nodes.
    """

    analysis_id: str
    account_id: str
    tenant_id: str
    interaction_ids: List[str]
    codes: List[Dict[str, Any]]
    themes: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    errors: List[str]
