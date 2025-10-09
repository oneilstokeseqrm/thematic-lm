"""LangGraph StateGraph definition for analysis pipeline."""

from langgraph.graph import StateGraph

from ..utils import get_logger

from .nodes import (
    aggregate_codes,
    aggregate_themes,
    coder_agent,
    load_interactions,
    reviewer_agent,
    theme_coder_agent,
)
from .state import PipelineState

logger = get_logger(__name__)


def create_pipeline_graph() -> StateGraph:
    """Create and configure the LangGraph pipeline.

    Returns:
        Compiled StateGraph ready for execution

    Note:
        TODO: Phase B - Configure PostgresSaver for checkpointing
    """
    # Create graph with PipelineState schema
    graph = StateGraph(PipelineState)

    # Add nodes
    graph.add_node("load_interactions", load_interactions)
    graph.add_node("coder", coder_agent)
    graph.add_node("aggregate_codes", aggregate_codes)
    graph.add_node("reviewer", reviewer_agent)
    graph.add_node("theme_coder", theme_coder_agent)
    graph.add_node("aggregate_themes", aggregate_themes)

    # Define edges (sequential flow)
    graph.set_entry_point("load_interactions")
    graph.add_edge("load_interactions", "coder")
    graph.add_edge("coder", "aggregate_codes")
    graph.add_edge("aggregate_codes", "reviewer")
    graph.add_edge("reviewer", "theme_coder")
    graph.add_edge("theme_coder", "aggregate_themes")
    graph.set_finish_point("aggregate_themes")

    # Compile graph
    compiled_graph = graph.compile()

    logger.info("Pipeline graph created and compiled")

    return compiled_graph
