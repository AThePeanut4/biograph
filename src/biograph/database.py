import logging
import typing
from typing import Annotated, Any, LiteralString, cast

import neo4j
from fastapi import Depends
from pydantic import BaseModel

from . import config
from .models import Graph, Node, Relationship

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
        return self.driver.session()

    def log_summary(self, summary: neo4j.ResultSummary):
        logger.info(
            "Query `%s` completed in %d ms",
            summary.query,
            summary.result_available_after,
        )

    def query(
        self,
        session: neo4j.Session,
        q: str,
        params: dict[str, typing.Any] | None = None,
    ) -> list[Any]:
        result = session.run(cast(LiteralString, q), params)
        values = result.data()

        summary = result.consume()
        self.log_summary(summary)

        return values

    def query_single(
        self,
        session: neo4j.Session,
        q: str,
        params: dict[str, typing.Any] | None = None,
    ) -> Any:
        result = session.run(cast(LiteralString, q), params)
        values = result.value()[0]

        summary = result.consume()
        self.log_summary(summary)

        return values

    def query_graph(
        self,
        session: neo4j.Session,
        q: str,
        params: dict[str, typing.Any] | None = None,
    ) -> Graph:
        result = session.run(cast(LiteralString, q), params)
        graph = result.graph()

        summary = result.consume()
        self.log_summary(summary)

        return Graph.from_neo4j(graph)

    def query_node(
        self,
        session: neo4j.Session,
        q: str,
        params: dict[str, typing.Any] | None = None,
    ) -> Node:
        result = session.run(cast(LiteralString, q), params)
        node = result.value()[0]

        summary = result.consume()
        self.log_summary(summary)

        return Node.from_neo4j(node)

    def query_nodes(
        self,
        session: neo4j.Session,
        q: str,
        params: dict[str, typing.Any] | None = None,
    ) -> list[Node]:
        result = session.run(cast(LiteralString, q), params)
        nodes = result.value()

        summary = result.consume()
        self.log_summary(summary)

        return [Node.from_neo4j(n) for n in nodes]

    def query_relationship(
        self,
        session: neo4j.Session,
        q: str,
        params: dict[str, typing.Any] | None = None,
    ) -> Relationship:
        result = session.run(cast(LiteralString, q), params)
        node = result.value()[0]

        summary = result.consume()
        self.log_summary(summary)

        return Relationship.from_neo4j(node)

    def query_relationships(
        self,
        session: neo4j.Session,
        q: str,
        params: dict[str, typing.Any] | None = None,
    ) -> list[Relationship]:
        result = session.run(cast(LiteralString, q), params)
        nodes = result.value()

        summary = result.consume()
        self.log_summary(summary)

        return [Relationship.from_neo4j(n) for n in nodes]

    def get_max_tag(self) -> int:
        with self.session() as session:
            ret = self.query_single(session, "MATCH (n: Model) RETURN max(n.tag)")
            return int(ret or 0)

    def get_graph(self) -> Graph:
        with self.session() as session:
            return self.query_graph(
                session, "MATCH (n) OPTIONAL MATCH (n)-[r]-() RETURN n, r"
            )

    def get_model_by_name(self, name: str) -> Graph:
        with self.session() as session:
            return self.query_graph(
                session,
                "MATCH (n:Model {name: $name}) "
                "MATCH (m{tag: n.tag}) "
                "OPTIONAL MATCH (m)-[r]-() "
                "RETURN m, r",
                {"name": name},
            )

    def get_model_by_node(self, label: str, property: str, value: str) -> Graph:
        with self.session() as session:
            if not label.isalnum():
                raise ValueError("invalid label")
            if not property.isalnum():
                raise ValueError("invalid label")

            return self.query_graph(
                session,
                f"MATCH (n:{label} {{{property}: $value}}) "
                "MATCH (m{tag: n.tag}) "
                "OPTIONAL MATCH (m)-[r]-() "
                "RETURN m, r",
                {"label": label, "property": property, "value": value},
            )

    def get_nodes(self) -> list[Node]:
        with self.session() as session:
            return self.query_nodes(session, "MATCH (n) RETURN n")

    def get_node_by_id(self, node_id: str) -> Node:
        with self.session() as session:
            return self.query_node(
                session,
                "MATCH (n) WHERE elementId(n) = $id RETURN n",
                {"id": node_id},
            )

    def get_relationships(self) -> list[Relationship]:
        with self.session() as session:
            return self.query_relationships(session, "MATCH ()-[r]-() RETURN r")

    def get_relationship_by_id(self, relationship_id: str) -> Relationship:
        with self.session() as session:
            return self.query_relationship(
                session,
                "MATCH ()-[r]-() WHERE elementId(n) = $id RETURN r",
                {"id": relationship_id},
            )


def get_db():
    cfg = Config.get()

    with Database(cfg) as db:
        yield db


DbDep = Annotated[Database, Depends(get_db)]
