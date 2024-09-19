import logging
from typing import cast

import neo4j.graph
import networkx as nx

from .edges import Edge
from .nodes import Node

logger = logging.getLogger(__name__)


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


def merge_nodes(
    graph: nx.MultiDiGraph,
    uuids: list[str],
    session: neo4j.Session | None = None,
):
    if len(uuids) < 2:
        return

    dst = cast(Node, graph.nodes[uuids[0]]["node"])

    for src_uuid in uuids[1:]:
        for edges in graph.succ[src_uuid].values():
            for edgedict in edges.values():
                edge = cast(Edge, edgedict["edge"])
                graph.add_edge(
                    dst.uuid,
                    edge.end_node,
                    key=edge.uuid,
                    edge=edge,
                )
        for edges in graph.pred[src_uuid].values():
            for edgedict in edges.values():
                edge = cast(Edge, edgedict["edge"])
                graph.add_edge(
                    edge.start_node,
                    dst.uuid,
                    key=edge.uuid,
                    edge=edge,
                )
        graph.remove_node(src_uuid)

    return graph
