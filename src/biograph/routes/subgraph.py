from fastapi import APIRouter

from .. import database
from ..api_models import Graph

router = APIRouter(prefix="/subgraph", tags=["subgraph"])


@router.get("/by-identifier")
def subgraphs_by_identifier(db: database.DbDep, identifier: str) -> Graph:
    with db.session() as session:
        g = database.get_subgraphs_by_identifier(session, identifier)
    return Graph.from_graph(g)
