import logging

import neo4j
from fastapi import APIRouter

from .. import database, graph
from ..api_models import Graph, MergeNodesInput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/merge", tags=["merge"])


@router.post("/nodes")
def merge_nodes(db: database.DbDep, input: MergeNodesInput) -> Graph:
    if input.apply:
        access_mode = neo4j.WRITE_ACCESS
    else:
        access_mode = neo4j.READ_ACCESS
    with db.session(access_mode) as session:
        g = database.get_nodes_with_neighbours(session, input.uuids)
        graph.merge_nodes(g, input.uuids, session if input.apply else None)

    return Graph.from_graph(g)
