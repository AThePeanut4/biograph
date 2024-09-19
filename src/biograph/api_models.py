import logging

import neo4j.graph
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Node(BaseModel):
    id: str
    label: str
    properties: dict[str, str]

    @classmethod
    def from_neo4j(cls, node: neo4j.graph.Node):
        return cls(
            id=node.element_id,
            label=next(iter(node.labels)),
            properties=dict(node.items()),
        )


class Relationship(BaseModel):
    id: str
    type: str
    start_node: str
    end_node: str
    properties: dict[str, str]

    @classmethod
    def from_neo4j(cls, relationship: neo4j.graph.Relationship):
        start_node, end_node = relationship.nodes
        if start_node is None:
            raise ValueError("relationship must have a start node")
        if end_node is None:
            raise ValueError("relationship must have an end node")

        return cls(
            id=relationship.element_id,
            type=relationship.type,
            start_node=start_node.element_id,
            end_node=end_node.element_id,
            properties=dict(relationship.items()),
        )


class Graph(BaseModel):
    nodes: list[Node]
    relationships: list[Relationship]

    @classmethod
    def from_neo4j(cls, graph: neo4j.graph.Graph):
        nodes = [Node.from_neo4j(n) for n in graph.nodes]
        relationships = [Relationship.from_neo4j(r) for r in graph.relationships]
        return cls(nodes=nodes, relationships=relationships)
