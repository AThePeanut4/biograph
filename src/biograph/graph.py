import neo4j.graph
import networkx as nx

from .edges import Edge
from .nodes import Node


def neo4j_to_networkx(graph: neo4j.graph.Graph) -> nx.MultiDiGraph:
    ret = nx.MultiDiGraph()
    for n in graph.nodes:
        node = Node.from_neo4j(n)
        ret.add_node(
            node.uuid,
            node=node,
        )
    for r in graph.relationships:
        edge = Edge.from_neo4j(r)
        ret.add_edge(
            edge.start_node,
            edge.end_node,
            key=edge.uuid,
            edge=edge,
        )
    return ret
