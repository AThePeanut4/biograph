from fastapi import APIRouter

from ..database import DbDep
from ..models import Node

router = APIRouter(prefix="/node", tags=["node"])


@router.get("/")
def nodes(db: DbDep) -> list[Node]:
    return db.get_nodes()


@router.get("/by-id/{node_id}")
def node_by_id(db: DbDep, node_id: str) -> Node:
    return db.get_node_by_id(node_id)
