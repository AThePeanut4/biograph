import logging
from typing import Any

import neo4j.graph

from .utils import get_subclasses

logger = logging.getLogger(__name__)


class Edge:
    element_id: str

    typ: str
    start_node: str
    end_node: str
    properties: dict[str, Any]

    def __init__(
        self,
        typ: str,
        element_id: str,
        start_node: str,
        end_node: str,
        properties: dict[str, str],
    ) -> None:
        self.element_id = element_id
        self.typ = typ
        self.start_node = start_node
        self.end_node = end_node
        self.properties = properties

    @staticmethod
    def from_neo4j(relationship: neo4j.graph.Relationship):
        element_id = relationship.element_id

        typ = relationship.type

        start_node, end_node = relationship.nodes
        if start_node is None:
            raise ValueError("relationship must have a start node")
        if end_node is None:
            raise ValueError("relationship must have an end node")

        properties = dict(relationship.items())

        for sub in get_subclasses(Edge):
            if sub.__name__ == typ:
                return sub(
                    element_id,
                    typ,
                    start_node.element_id,
                    end_node.element_id,
                    properties,
                )

        return Edge(
            element_id,
            typ,
            start_node.element_id,
            end_node.element_id,
            properties,
        )
