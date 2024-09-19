from fastapi import APIRouter

from .. import database
from ..api_models import Node

router = APIRouter(prefix="/node", tags=["nodes"])


@router.get("/all")
def all_nodes(db: database.DbDep) -> list[Node]:
    with db.session() as session:
        return [Node.from_node(n) for n in database.get_nodes(session)]


@router.get("/by-id/{node_uuid}")
def node_by_uuid(db: database.DbDep, node_id: str) -> Node:
    with db.session() as session:
        n = database.get_node(session, node_id)
    return Node.from_node(n)
