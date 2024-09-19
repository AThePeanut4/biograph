import itertools
import logging
from collections import Counter
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


def _calc_similarity(graph: nx.MultiDiGraph, a: str, b: str) -> float:
    a_succ: dict[str, list[str]] = {}
    for nbr, edges in graph.succ[a].items():
        nbr_node = cast(Node, graph.nodes[nbr]["node"])
        for edgedict in edges.values():
            edge = cast(Edge, edgedict["edge"])
            if nbr_node.label in a_succ:
                a_succ[nbr_node.label].append(edge.typ)
            else:
                a_succ[nbr_node.label] = [edge.typ]

    a_pred: dict[str, list[str]] = {}
    for nbr, edges in graph.pred[a].items():
        nbr_node = cast(Node, graph.nodes[nbr]["node"])
        for edgedict in edges.values():
            edge = cast(Edge, edgedict["edge"])
            if nbr_node.label in a_pred:
                a_pred[nbr_node.label].append(edge.typ)
            else:
                a_pred[nbr_node.label] = [edge.typ]

    b_succ: dict[str, list[str]] = {}
    for nbr, edges in graph.succ[b].items():
        nbr_node = cast(Node, graph.nodes[nbr]["node"])
        for edgedict in edges.values():
            edge = cast(Edge, edgedict["edge"])
            if nbr_node.label in b_succ:
                b_succ[nbr_node.label].append(edge.typ)
            else:
                b_succ[nbr_node.label] = [edge.typ]

    b_pred: dict[str, list[str]] = {}
    for nbr, edges in graph.pred[b].items():
        nbr_node = cast(Node, graph.nodes[nbr]["node"])
        for edgedict in edges.values():
            edge = cast(Edge, edgedict["edge"])
            if nbr_node.label in b_pred:
                b_pred[nbr_node.label].append(edge.typ)
            else:
                b_pred[nbr_node.label] = [edge.typ]

    score = 0
    max_score = 0

    for label in set(a_succ.keys()) | set(b_succ.keys()):
        a_types = a_succ.get(label, [])
        a_counter = Counter(a_types)
        b_types = b_succ.get(label, [])
        b_counter = Counter(b_types)

        intersect_counter = a_counter & b_counter
        common_count = intersect_counter.total()

        a_uncommon_count = len(a_types) - common_count
        b_uncommon_count = len(b_types) - common_count

        uncommon_count = min(a_uncommon_count, b_uncommon_count)

        extra_count = abs(a_uncommon_count - uncommon_count)

        score += 3 * common_count + 2 * uncommon_count - extra_count
        max_score += 3 * max(len(a_types), len(b_types))

    for label in set(a_pred.keys()) | set(b_pred.keys()):
        a_types = a_pred.get(label, [])
        a_counter = Counter(a_types)
        b_types = b_pred.get(label, [])
        b_counter = Counter(b_types)

        intersect_counter = a_counter & b_counter
        common_count = intersect_counter.total()

        a_uncommon_count = len(a_types) - common_count
        b_uncommon_count = len(b_types) - common_count

        uncommon_count = min(a_uncommon_count, b_uncommon_count)

        extra_count = abs(a_uncommon_count - uncommon_count)

        score += 3 * common_count + uncommon_count - extra_count
        max_score += 3 * max(len(a_types), len(b_types))

    s = score / max_score * 100
    logger.debug("_calc_similarity(%s, %s) == %d", a, b, s)
    return s


def calc_similarity(
    graph: nx.MultiDiGraph,
    uuids: list[str],
) -> int:
    score = 0
    i = 0

    for a, b in itertools.combinations(uuids, 2):
        score += _calc_similarity(graph, a, b)
        i += 1

    return max(int(score / i), 0)


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
