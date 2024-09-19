import logging
from typing import Any

import neo4j.graph

from .utils import get_subclasses

logger = logging.getLogger(__name__)


class Edge:
    uuid: str

    typ: str
    start_node: str
    end_node: str
    properties: dict[str, Any]

    def __init__(
        self,
        typ: str,
        uuid: str,
        start_node: str,
        end_node: str,
        properties: dict[str, str],
    ) -> None:
        self.uuid = uuid
        self.typ = typ
        self.start_node = start_node
        self.end_node = end_node
        self.properties = properties

    @staticmethod
    def from_neo4j(relationship: neo4j.graph.Relationship):
        properties = dict(relationship.items())

        if "uuid" not in properties:
            raise ValueError(f"relationship {relationship.element_id} has no UUID")

        uuid = properties.pop("uuid")

        typ = relationship.type
        typ_name = typ.casefold().replace("_", "")

        start_node, end_node = relationship.nodes
        if start_node is None:
            raise ValueError(f"relationship {uuid} has no start node")
        if end_node is None:
            raise ValueError(f"relationship {uuid} has no end node")

        start_node = start_node.get("uuid")
        if start_node is None:
            raise ValueError(f"relationship {uuid} start node has no UUID")
        end_node = end_node.get("uuid")
        if end_node is None:
            raise ValueError(f"relationship {uuid} end node has no UUID")

        for sub in get_subclasses(Edge):
            if sub.__name__.casefold() == typ_name:
                return sub(uuid, typ, start_node, end_node, properties)

        return Edge(uuid, typ, start_node, end_node, properties)


class HasCompartment(Edge):
    pass


class HasKineticLaw(Edge):
    pass


class HasParameter(Edge):
    pass


class HasProduct(Edge):
    pass


class HasReaction(Edge):
    pass


class HasSpecies(Edge):
    pass


class HasUnits(Edge):
    pass


class InCompartment(Edge):
    pass


class IsComposed(Edge):
    pass


class IsReactant(Edge):
    pass
