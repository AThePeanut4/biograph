from __future__ import annotations

import logging
from lxml import etree as xml

import neo4j.graph

from .utils import get_subclasses

logger = logging.getLogger(__name__)

ANNOTATION_NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "bqbiol": "http://biomodels.net/biology-qualifiers/",
    "bqmodel": "http://biomodels.net/model-qualifiers/",
}


class Node:
    uuid: str

    label: str
    properties: dict[str, str]

    annotation: xml._Element | None
    id: str | None
    metaid: str | None
    name: str | None

    identifiers: list[str]

    def __init__(self, uuid: str, label: str, properties: dict[str, str]) -> None:
        self.uuid = uuid
        self.label = label
        self.properties = properties

        annotation = properties.get("annotation")
        if annotation is not None:
            self.annotation = xml.fromstring(annotation)
        else:
            self.annotation = None

        self.id = properties.get("id")
        self.metaid = properties.get("metaid")
        self.name = properties.get("name")

        self.identifiers = []
        if self.annotation is not None and self.metaid:
            for el in self.annotation.xpath(
                "rdf:RDF/rdf:Description[@rdf:about=$metaid]/bqbiol:is/rdf:Bag/rdf:li/@rdf:resource",
                metaid=f"#{self.metaid}",
                namespaces=ANNOTATION_NS,
            ):
                self.identifiers.append(str(el))

    @staticmethod
    def from_neo4j(node: neo4j.graph.Node) -> Node:
        properties = dict(node.items())

        if "uuid" not in properties:
            raise ValueError(f"node {node.element_id} has no UUID")

        uuid = properties.pop("uuid")

        labels = node.labels
        if len(labels) == 0:
            logger.warning("node %s has no labels", uuid)
            label = "Node"
        else:
            if len(labels) > 1:
                logger.warning("node %s has >1 labels (%d)", uuid, len(labels))
            label = next(iter(node.labels))

        for sub in get_subclasses(Node):
            if sub.__name__ == label:
                return sub(uuid, label, properties)

        return Node(uuid, label, properties)


class Model(Node):
    def __init__(self, uuid: str, label: str, properties: dict[str, str]) -> None:
        super().__init__(uuid, label, properties)

        if self.annotation is not None and self.metaid:
            for el in self.annotation.xpath(
                "rdf:RDF/rdf:Description[@rdf:about=$metaid]/bqmodel:is/rdf:Bag/rdf:li/@rdf:resource",
                metaid=f"#{self.metaid}",
                namespaces=ANNOTATION_NS,
            ):
                self.identifiers.append(str(el))


class Compartment(Node):
    size: float | None

    def __init__(self, uuid: str, label: str, properties: dict[str, str]) -> None:
        super().__init__(uuid, label, properties)

        size = properties.get("size")
        if size is not None:
            self.size = float(size)
        else:
            self.size = None


class Species(Node):
    pass


class Reaction(Node):
    reversible: bool | None

    def __init__(self, uuid: str, label: str, properties: dict[str, str]) -> None:
        super().__init__(uuid, label, properties)

        reversible = properties.get("reversible")
        if reversible is not None:
            self.reversible = bool(reversible)
        else:
            self.reversible = None


class KineticLaw(Node):
    formula: str | None

    def __init__(self, uuid: str, label: str, properties: dict[str, str]) -> None:
        super().__init__(uuid, label, properties)

        self.formula = properties.get("formula")


class Parameter(Node):
    value: str | None

    def __init__(self, uuid: str, label: str, properties: dict[str, str]) -> None:
        super().__init__(uuid, label, properties)

        self.value = properties.get("value")


class UnitDefinition(Node):
    pass


class Unit(Node):
    exponent: int | None
    kind: int | None
    multiplier: float | None
    scale: int | None

    def __init__(self, uuid: str, label: str, properties: dict[str, str]) -> None:
        super().__init__(uuid, label, properties)

        exponent = properties.get("exponent")
        if exponent is not None:
            self.exponent = int(exponent)
        else:
            self.exponent = None

        kind = properties.get("kind")
        if kind is not None:
            self.kind = int(kind)
        else:
            self.kind = None

        multiplier = properties.get("multiplier")
        if multiplier is not None:
            self.multiplier = float(multiplier)
        else:
            self.multiplier = None

        scale = properties.get("scale")
        if scale is not None:
            self.scale = int(scale)
        else:
            self.scale = None
