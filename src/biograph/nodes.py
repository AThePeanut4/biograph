from __future__ import annotations

import logging

import neo4j.graph

logger = logging.getLogger(__name__)


class Node:
    element_id: str

    label: str
    properties: dict[str, str]

    id: str | None
    metaid: str | None
    name: str | None

    def __init__(self, element_id: str, label: str, properties: dict[str, str]) -> None:
        self.element_id = element_id
        self.label = label
        self.properties = properties

        self.id = properties.get("id")
        self.metaid = properties.get("metaid")
        self.name = properties.get("name")

    @staticmethod
    def from_neo4j(node: neo4j.graph.Node) -> Node:
        element_id = node.element_id

        labels = node.labels
        if len(labels) == 0:
            logger.warning("node %s has no labels", node.element_id)
            label = "Node"
        else:
            if len(labels) > 1:
                logger.warning(
                    "node %s has >1 labels (%d)", node.element_id, len(labels)
                )
            label = next(iter(node.labels))

        properties = dict(node.items())

        return Node(element_id, label, properties)
