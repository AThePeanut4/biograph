import logging
from typing import Any

from fastapi import APIRouter

from ..api_models import Graph, Node, Relationship
from ..database import DbDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["queries"])


@router.get("/raw")
def raw_query(db: DbDep, q: str) -> list[Any]:
    with db.session() as session:
        return db.query(session, q)


@router.get("/graph")
def graph_query(db: DbDep, q: str) -> Graph:
    with db.session() as session:
        g = db.query_graph(session, q)
        return Graph.from_graph(g)


@router.get("/nodes")
def nodes_query(db: DbDep, q: str) -> list[Node]:
    with db.session() as session:
        return [Node.from_node(n) for n in db.query_nodes(session, q)]


@router.get("/relationships")
def relationships_query(db: DbDep, q: str) -> list[Relationship]:
    with db.session() as session:
        return [Relationship.from_edge(e) for e in db.query_relationships(session, q)]
