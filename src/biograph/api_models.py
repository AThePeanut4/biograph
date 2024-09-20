import logging

import networkx as nx
from pydantic import BaseModel

from . import nodes, edges

logger = logging.getLogger(__name__)


class Node(BaseModel):
    id: str
    label: str
    properties: dict[str, str]
    identifiers: list[str]

    @classmethod
    def from_node(cls, node: nodes.Node):
        return cls(
            id=node.uuid,
            label=node.label,
            properties=node.properties,
            identifiers=node.identifiers,
        )


class Relationship(BaseModel):
    id: str
    type: str
    start_node: str
    end_node: str
    properties: dict[str, str]

    @classmethod
    def from_edge(cls, edge: edges.Edge):
        return cls(
            id=edge.uuid,
            type=edge.typ,
            start_node=edge.start_node,
            end_node=edge.end_node,
            properties=edge.properties,
        )


class Graph(BaseModel):
    nodes: list[Node]
    relationships: list[Relationship]

    @classmethod
    def from_graph(cls, g: nx.MultiDiGraph):
        nodes = [Node.from_node(n) for _, n in g.nodes.data("node")]
        relationships = [Relationship.from_edge(e) for _, _, e in g.edges.data("edge")]
        return cls(nodes=nodes, relationships=relationships)


class MergeNodesInput(BaseModel):
    uuids: list[str]
    apply: bool = False


class CalculateSimilarityInput(BaseModel):
    uuids: list[str]
