from fastapi import APIRouter

from ..database import DbDep
from ..models import Relationship

router = APIRouter(prefix="/relationship", tags=["relationship"])


@router.get("/")
def relationships(db: DbDep) -> list[Relationship]:
    return db.get_relationships()


@router.get("/by-id/{relationship_id}")
def relationship_by_id(db: DbDep, relationship_id: str) -> Relationship:
    return db.get_relationship_by_id(relationship_id)
