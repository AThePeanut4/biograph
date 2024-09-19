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

    def session(self) -> neo4j.Session:
        return self.driver.session(default_access_mode=neo4j.READ_ACCESS)

    def rw_session(self) -> neo4j.Session:
        return self.driver.session(default_access_mode=neo4j.WRITE_ACCESS)

    @classmethod
    def log_summary(cls, summary: neo4j.ResultSummary):
        logger.info(
            "Query `%s` completed in %d ms",
            summary.query,
            summary.result_available_after,
        )

    @classmethod
    def query(
        cls,
        session: neo4j.Session,
        q: str,
        params: dict[str, typing.Any] | None = None,
    ) -> list[Any]:
        result = session.run(cast(LiteralString, q), params)
        values = result.data()

        summary = result.consume()
        cls.log_summary(summary)

        return values

    @classmethod
    def query_single(
        cls,
        session: neo4j.Session,
        q: str,
        params: dict[str, typing.Any] | None = None,
    ) -> Any:
        result = session.run(cast(LiteralString, q), params)
        values = result.value()[0]

        summary = result.consume()
        cls.log_summary(summary)

        return values

    @classmethod
    def query_graph(
        cls,
        session: neo4j.Session,
        q: str,
        params: dict[str, typing.Any] | None = None,
    ) -> nx.MultiDiGraph:
        result = session.run(cast(LiteralString, q), params)
        g = result.graph()

        summary = result.consume()
        cls.log_summary(summary)

        return graph.neo4j_to_networkx(g)

    @classmethod
    def query_node(
        cls,
        session: neo4j.Session,
        q: str,
        params: dict[str, typing.Any] | None = None,
    ) -> Node:
        result = session.run(cast(LiteralString, q), params)
        node = result.value()[0]

        summary = result.consume()
        cls.log_summary(summary)

        return Node.from_neo4j(node)

    @classmethod
    def query_nodes(
        cls,
        session: neo4j.Session,
        q: str,
        params: dict[str, typing.Any] | None = None,
    ) -> list[Node]:
        result = session.run(cast(LiteralString, q), params)
        nodes = result.value()

        summary = result.consume()
        cls.log_summary(summary)

        return [Node.from_neo4j(n) for n in nodes]

    @classmethod
    def query_relationship(
        cls,
        session: neo4j.Session,
        q: str,
        params: dict[str, typing.Any] | None = None,
    ) -> Edge:
        result = session.run(cast(LiteralString, q), params)
        node = result.value()[0]

        summary = result.consume()
        cls.log_summary(summary)

        return Edge.from_neo4j(node)

    @classmethod
    def query_relationships(
        cls,
        session: neo4j.Session,
        q: str,
        params: dict[str, typing.Any] | None = None,
    ) -> list[Edge]:
        result = session.run(cast(LiteralString, q), params)
        nodes = result.value()

        summary = result.consume()
        cls.log_summary(summary)

        return [Edge.from_neo4j(n) for n in nodes]

    @classmethod
    def get_max_tag(cls, session: neo4j.Session) -> int:
        ret = cls.query_single(session, "MATCH (n: Model) RETURN max(n.tag)")
        return int(ret or 0)

    @classmethod
    def get_graph(cls, session: neo4j.Session) -> nx.MultiDiGraph:
        return cls.query_graph(
            session, "MATCH (n) OPTIONAL MATCH (n)-[r]-() RETURN n, r"
        )

    @classmethod
    def get_model_by_name(cls, session: neo4j.Session, name: str) -> nx.MultiDiGraph:
        return cls.query_graph(
            session,
            "MATCH (n:Model {name: $name}) "
            "MATCH (m{tag: n.tag}) "
            "OPTIONAL MATCH (m)-[r]-() "
            "RETURN m, r",
            {"name": name},
        )

    @classmethod
    def get_model_by_node(
        cls, session: neo4j.Session, label: str, property: str, value: str
    ) -> nx.MultiDiGraph:
        if not label.isalnum():
            raise ValueError("invalid label")
        if not property.isalnum():
            raise ValueError("invalid property")

        return cls.query_graph(
            session,
            f"MATCH (n:{label} {{{property}: $value}}) "
            "MATCH (m{tag: n.tag}) "
            "OPTIONAL MATCH (m)-[r]-() "
            "RETURN m, r",
            {"label": label, "property": property, "value": value},
        )

    @classmethod
    def get_model_by_node_id(
        cls, session: neo4j.Session, node_id: str
    ) -> nx.MultiDiGraph:
        return cls.query_graph(
            session,
            "MATCH (n) WHERE elementId(n) = $id"
            "MATCH (m{tag: n.tag}) "
            "OPTIONAL MATCH (m)-[r]-() "
            "RETURN m, r",
            {"id": node_id},
        )

    @classmethod
    def get_model_by_tag(cls, session: neo4j.Session, tag: str) -> nx.MultiDiGraph:
        return cls.query_graph(
            session,
            "MATCH (m{tag: $tag}) OPTIONAL MATCH (m)-[r]-() RETURN m, r",
            {"tag": tag},
        )

    @classmethod
    def get_nodes(cls, session: neo4j.Session) -> list[Node]:
        return cls.query_nodes(session, "MATCH (n) RETURN n")

    @classmethod
    def get_node_by_id(cls, session: neo4j.Session, node_id: str) -> Node:
        return cls.query_node(
            session,
            "MATCH (n) WHERE elementId(n) = $id RETURN n",
            {"id": node_id},
        )

    @classmethod
    def get_relationships(cls, session: neo4j.Session) -> list[Edge]:
        return cls.query_relationships(session, "MATCH ()-[r]-() RETURN r")

    @classmethod
    def get_relationship_by_id(
        cls, session: neo4j.Session, relationship_id: str
    ) -> Edge:
        return cls.query_relationship(
            session,
            "MATCH ()-[r]-() WHERE elementId(n) = $id RETURN r",
            {"id": relationship_id},
        )


def get_db():
    cfg = Config.get()

    with Database(cfg) as db:
        yield db


DbDep = Annotated[Database, Depends(get_db)]
