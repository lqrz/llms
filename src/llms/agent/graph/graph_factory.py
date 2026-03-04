"""Graph factory."""

from typing import Literal

from llms.agent.graph.graph_builds import build_basic_graph, build_rag_graph


class GraphFactory:
    """Graph factory."""

    @classmethod
    def instantiate_graph(cls, workflow_type: Literal["basic", "rag"], **kwargs):
        """Instantiate graph."""
        assert isinstance(workflow_type, str)
        if workflow_type == "basic":
            return build_basic_graph(**kwargs)
        if workflow_type == "rag":
            return build_rag_graph(**kwargs)
