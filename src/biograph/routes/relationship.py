from fastapi import APIRouter

from .. import database
from ..api_models import Relationship

router = APIRouter(prefix="/relationship", tags=["relationships"])


@router.get("/all")
def all_relationships(db: database.DbDep) -> list[Relationship]:
    with db.session() as session:
        return [Relationship.from_edge(e) for e in database.get_relationships(session)]


@router.get("/by-id/{relationship_uuid}")
def relationship_by_uuid(db: database.DbDep, relationship_uuid: str) -> Relationship:
    with db.session() as session:
        e = database.get_relationship(session, relationship_uuid)
    return Relationship.from_edge(e)
