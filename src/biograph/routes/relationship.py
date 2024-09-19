from fastapi import APIRouter

from ..api_models import Relationship
from ..database import DbDep

router = APIRouter(prefix="/relationship", tags=["relationships"])


@router.get("/all")
def all_relationships(db: DbDep) -> list[Relationship]:
    return [Relationship.from_edge(e) for e in db.get_relationships()]


@router.get("/by-id/{relationship_id}")
def relationship_by_id(db: DbDep, relationship_id: str) -> Relationship:
    e = db.get_relationship_by_id(relationship_id)
    return Relationship.from_edge(e)
