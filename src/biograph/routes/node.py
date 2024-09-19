from fastapi import APIRouter

from ..api_models import Node
from ..database import DbDep

router = APIRouter(prefix="/node", tags=["nodes"])


@router.get("/all")
def all_nodes(db: DbDep) -> list[Node]:
    return [Node.from_node(n) for n in db.get_nodes()]


@router.get("/by-id/{node_id}")
def node_by_id(db: DbDep, node_id: str) -> Node:
    n = db.get_node_by_id(node_id)
    return Node.from_node(n)
