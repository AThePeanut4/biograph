from fastapi import APIRouter

from .. import database
from ..api_models import Relationship

router = APIRouter(prefix="/relationship", tags=["relationships"])


@router.get("/all")
def all_relationships(db: database.DbDep) -> list[Relationship]:
    with db.session() as session:
        return [Relationship.from_edge(e) for e in database.get_relationships(session)]


@router.get("/by-id/{relationship_id}")
def relationship_by_id(db: database.DbDep, relationship_id: str) -> Relationship:
    with db.session() as session:
        e = database.get_relationship_by_id(session, relationship_id)
    return Relationship.from_edge(e)
