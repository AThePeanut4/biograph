import logging
from typing import Any

from fastapi import APIRouter

from ..database import DbDep
from ..models import Graph, Node, Relationship

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


@router.get("/raw")
def raw_query(db: DbDep, q: str) -> list[Any]:
    with db.session() as session:
        return db.query(session, q)


@router.get("/graph")
def graph_query(db: DbDep, q: str) -> Graph:
    with db.session() as session:
        return db.query_graph(session, q)


@router.get("/nodes")
def nodes_query(db: DbDep, q: str) -> list[Node]:
    with db.session() as session:
        return db.query_nodes(session, q)


@router.get("/relationships")
def relationships_query(db: DbDep, q: str) -> list[Relationship]:
    with db.session() as session:
        return db.query_relationships(session, q)
