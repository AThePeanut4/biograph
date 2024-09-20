import logging
from typing import Any

from fastapi import APIRouter

from .. import database
from ..api_models import Graph, Node, Relationship

logger = logging.getLogger(__name__)

#######################
## /query API routes ##
#######################

router = APIRouter(prefix="/query", tags=["queries"])


@router.get("/raw")
def raw_query(db: database.DbDep, q: str) -> list[Any]:
    with db.session() as session:
        return database.query(session, q)


@router.get("/graph")
def graph_query(db: database.DbDep, q: str) -> Graph:
    with db.session() as session:
        g = database.query_graph(session, q)
        return Graph.from_graph(g)


@router.get("/nodes")
def nodes_query(db: database.DbDep, q: str) -> list[Node]:
    with db.session() as session:
        return [Node.from_node(n) for n in database.query_nodes(session, q)]


@router.get("/relationships")
def relationships_query(db: database.DbDep, q: str) -> list[Relationship]:
    with db.session() as session:
        return [
            Relationship.from_edge(e) for e in database.query_relationships(session, q)
        ]
