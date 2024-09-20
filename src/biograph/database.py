import logging
import typing
from typing import Annotated, Any, LiteralString, cast

import neo4j
import networkx as nx
from fastapi import Depends
from pydantic import BaseModel

from . import config, graph
from .edges import Edge
from .nodes import Node

logger = logging.getLogger(__name__)


class Config(BaseModel):
    uri: str
    database: str
    username: str
    password: str

    @classmethod
    def get(cls):
        return config.get(cls, "neo4j")


class Database:
    """Represents a database connection"""

    def __init__(self, cfg: Config):
        self.driver = neo4j.GraphDatabase.driver(
            cfg.uri,
            auth=(cfg.username, cfg.password),
            database=cfg.database,
        )

    def __enter__(self):
        try:
            self.driver.verify_connectivity()
        except:
            self.driver.close()
            raise
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.driver.close()

    def session(self, **kwargs) -> neo4j.Session:
        return self.driver.session(default_access_mode=neo4j.READ_ACCESS, **kwargs)

    def rw_session(self, **kwargs) -> neo4j.Session:
        return self.driver.session(default_access_mode=neo4j.WRITE_ACCESS, **kwargs)


def log_summary(summary: neo4j.ResultSummary):
    logger.info(
        "Query `%s` completed in %d ms",
        summary.query,
        summary.result_available_after,
    )


def query(
    session: neo4j.Session,
    q: str,
    params: dict[str, typing.Any] | None = None,
) -> list[Any]:
    """Execute a query returning arbitrary data"""
    result = session.run(cast(LiteralString, q), params)
    values = result.data()

    summary = result.consume()
    log_summary(summary)

    return values


def query_single(
    session: neo4j.Session,
    q: str,
    params: dict[str, typing.Any] | None = None,
) -> Any:
    """Execute a query returning one object"""
    result = session.run(cast(LiteralString, q), params)
    values = result.value()[0]

    summary = result.consume()
    log_summary(summary)

    return values


def query_graph(
    session: neo4j.Session,
    q: str,
    params: dict[str, typing.Any] | None = None,
) -> nx.MultiDiGraph:
    """Execute a query returning a graph"""
    result = session.run(cast(LiteralString, q), params)
    g = result.graph()

    summary = result.consume()
    log_summary(summary)

    return graph.neo4j_to_networkx(g)


def query_node(
    session: neo4j.Session,
    q: str,
    params: dict[str, typing.Any] | None = None,
) -> Node:
    """Execute a query returning a node"""
    result = session.run(cast(LiteralString, q), params)
    node = result.value()[0]

    summary = result.consume()
    log_summary(summary)

    return Node.from_neo4j(node)


def query_nodes(
    session: neo4j.Session,
    q: str,
    params: dict[str, typing.Any] | None = None,
) -> list[Node]:
    """Execute a query returning multiple nodes"""
    result = session.run(cast(LiteralString, q), params)
    nodes = result.value()

    summary = result.consume()
    log_summary(summary)

    return [Node.from_neo4j(n) for n in nodes]


def query_relationship(
    session: neo4j.Session,
    q: str,
    params: dict[str, typing.Any] | None = None,
) -> Edge:
    """Execute a query returning a relationship"""
    result = session.run(cast(LiteralString, q), params)
    node = result.value()[0]

    summary = result.consume()
    log_summary(summary)

    return Edge.from_neo4j(node)


def query_relationships(
    session: neo4j.Session,
    q: str,
    params: dict[str, typing.Any] | None = None,
) -> list[Edge]:
    """Execute a query returning multiple relationships"""
    result = session.run(cast(LiteralString, q), params)
    nodes = result.value()

    summary = result.consume()
    log_summary(summary)

    return [Edge.from_neo4j(n) for n in nodes]


def get_graph(session: neo4j.Session) -> nx.MultiDiGraph:
    """Return all nodes and relationships in the database"""
    return query_graph(session, "MATCH (n) OPTIONAL MATCH (n)-[r]-() RETURN n, r")


def get_model(session: neo4j.Session, uuid: str) -> nx.MultiDiGraph:
    """Return the entire model specified by the given uuid"""
    return query_graph(
        session,
        "MATCH (n:Model {uuid: $uuid}) "
        "CALL apoc.path.subgraphAll(n, {}) "
        "YIELD nodes, relationships "
        "RETURN nodes, relationships",
        {"uuid": uuid},
    )


def get_model_by_name(session: neo4j.Session, name: str) -> nx.MultiDiGraph:
    """Return all models with the given name"""
    return query_graph(
        session,
        "MATCH (n:Model {name: $name}) "
        "CALL apoc.path.subgraphAll(n, {}) "
        "YIELD nodes, relationships "
        "RETURN nodes, relationships",
        {"name": name},
    )


def get_model_by_node(
    session: neo4j.Session,
    label: str,
    property: str,
    value: str,
) -> nx.MultiDiGraph:
    """Return all models containing a node with the given attributes"""
    if not label.isalnum():
        raise ValueError("invalid label")
    if not property.isalnum():
        raise ValueError("invalid property")

    return query_graph(
        session,
        f"MATCH (n:{label} {{{property}: $value}}) "
        "CALL apoc.path.subgraphAll(n, {}) "
        "YIELD nodes, relationships "
        "RETURN nodes, relationships",
        {"label": label, "property": property, "value": value},
    )


def get_model_by_node_uuid(session: neo4j.Session, uuid: str) -> nx.MultiDiGraph:
    """Return all models containing the node with the given uuid"""
    return query_graph(
        session,
        "MATCH (n) WHERE n.uuid = $uuid "
        "CALL apoc.path.subgraphAll(n, {}) "
        "YIELD nodes, relationships "
        "RETURN nodes, relationships",
        {"uuid": uuid},
    )


def get_subgraphs_by_uuids(session: neo4j.Session, uuids: list[str]) -> nx.MultiDiGraph:
    """Return the nodes with the given uuids and their immediate neighbours"""
    return query_graph(
        session,
        "UNWIND $uuids AS uuid "
        "MATCH (n {uuid: uuid}) "
        "MATCH (n)-[r]-(m) "
        "RETURN n, r, m",
        {"uuids": uuids},
    )


def get_subgraphs_by_identifier(
    session: neo4j.Session, identifier: str
) -> nx.MultiDiGraph:
    """Return all nodes with the given identifier and their immediate neighbours"""
    graph = get_graph(session)

    uuids = []
    for n, node in graph.nodes.data("node"):
        node = cast(Node, node)
        if identifier in node.identifiers:
            uuids.append(n)

    return get_subgraphs_by_uuids(session, uuids)


def get_nodes(session: neo4j.Session) -> list[Node]:
    """Return all nodes in the database"""
    return query_nodes(session, "MATCH (n) RETURN n")


def get_node(session: neo4j.Session, uuid: str) -> Node:
    """Return the node with the given uuid"""
    return query_node(
        session,
        "MATCH (n) WHERE n.uuid = $uuid RETURN n",
        {"uuid": uuid},
    )


def merge_node(session: neo4j.Session, node: Node):
    """Create or update the given node"""
    uuid = node.uuid
    props = node.properties

    query(
        session,
        f"MERGE (n:{node.label} {{uuid: $uuid}}) "
        "ON CREATE SET n += $props "
        "ON MATCH SET n += $props",
        {"uuid": uuid, "props": props},
    )


def delete_node(session: neo4j.Session, node: Node):
    """Delete the given node"""
    query(
        session,
        "MATCH (n {uuid: $uuid}) DETACH DELETE n",
        {"uuid": node.uuid},
    )


def get_relationships(session: neo4j.Session) -> list[Edge]:
    """Return all relationships in the database"""
    return query_relationships(session, "MATCH ()-[r]-() RETURN r")


def get_relationship(session: neo4j.Session, uuid: str) -> Edge:
    """Return the relationship with the given uuid"""
    return query_relationship(
        session,
        "MATCH ()-[r]-() WHERE n.uuid = $uuid RETURN r",
        {"uuid": uuid},
    )


def merge_relationship(session: neo4j.Session, edge: Edge):
    """Create or update the given relationship"""
    start = edge.start_node
    end = edge.end_node
    uuid = edge.uuid
    props = edge.properties

    query(
        session,
        "MATCH (start{uuid: $start}) "
        "MATCH (end{uuid: $end}) "
        f"MERGE (start)-[r:{edge.typ} {{uuid: $uuid}}]->(end) "
        "ON CREATE SET r += $props "
        "ON MATCH SET r += $props",
        {"start": start, "end": end, "uuid": uuid, "props": props},
    )


def delete_relationship(session: neo4j.Session, edge: Edge):
    """Delete the given relationship"""
    query(
        session,
        "MATCH ()-(r{uuid: $uuid})-() DELETE r",
        {"uuid": edge.uuid},
    )


def delete_all(session: neo4j.Session):
    """Delete all nodes and relationships in the database"""
    query(session, "MATCH (n) DETACH DELETE n")


def assign_uuids_by_tag(session: neo4j.Session, tag: str):
    """Assign random uuids to all nodes with the given tag"""
    query(session, "MATCH (n{tag: $tag}) SET n.uuid = randomUUID()", {"tag": tag})
    query(session, "MATCH ()-[r{tag: $tag}]-() SET r.uuid = randomUUID()", {"tag": tag})


def delete_all_by_tag(session: neo4j.Session, tag: str):
    """Delete all nodes and relationships with the given tag"""
    query(session, "MATCH (n{tag: $tag}) DETACH DELETE n", {"tag": tag})
    query(session, "MATCH ()-[r{tag: $tag}]-() DELETE r", {"tag": tag})


def remove_tag(session: neo4j.Session, tag: str):
    """Remove the given tag from all nodes and relationships that have it"""
    query(session, "MATCH (n{tag: $tag}) REMOVE n.tag", {"tag": tag})
    query(session, "MATCH ()-[r{tag: $tag}]-() REMOVE r.tag", {"tag": tag})


def delete_dangling_nodes_by_tag(session: neo4j.Session, tag: str):
    """Remove all unreachable nodes with the given tag"""
    query(
        session,
        "MATCH (n{tag: $tag}) WHERE NOT EXISTS { (m:Model)-[*]-(n) } DETACH DELETE n",
        {"tag": tag},
    )


def get_db():
    cfg = Config.get()

    with Database(cfg) as db:
        yield db


# FastAPI dependency
DbDep = Annotated[Database, Depends(get_db)]
