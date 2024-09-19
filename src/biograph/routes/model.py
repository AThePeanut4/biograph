import logging

from fastapi import APIRouter, UploadFile

from .. import database
from ..api_models import Graph
from ..neo4jsbml import sbml_to_neo4j

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/model", tags=["models"])


@router.get("/all")
def models(db: database.DbDep) -> Graph:
    with db.session() as session:
        g = database.get_graph(session)
    return Graph.from_graph(g)


@router.get("/by-name/{model_name}")
def model_by_name(
    db: database.DbDep,
    model_name: str,
) -> Graph:
    with db.session() as session:
        g = database.get_model_by_name(session, model_name)
    return Graph.from_graph(g)


@router.get("/by-node")
def model_by_node(
    db: database.DbDep,
    label: str,
    property: str,
    value: str,
) -> Graph:
    with db.session() as session:
        g = database.get_model_by_node(session, label, property, value)
    return Graph.from_graph(g)


@router.get("/by-node-id/{node_id}")
def model_by_node_id(db: database.DbDep, node_id: str) -> Graph:
    with db.session() as session:
        g = database.get_model_by_node_id(session, node_id)
    return Graph.from_graph(g)


@router.get("/by-tag/{tag}")
def mode_by_tag(
    db: database.DbDep,
    tag: str,
) -> Graph:
    with db.session() as session:
        g = database.get_model_by_tag(session, tag)
    return Graph.from_graph(g)


@router.post("/upload")
async def upload(db: database.DbDep, file: UploadFile, schema: UploadFile | None = None) -> None:
    b = await file.read()
    xml = b.decode()

    with db.session() as session:
        tag = database.get_max_tag(session) + 1

    logger.info("Importing SBML, using tag %d", tag)

    if schema is not None:
        b = await schema.read()
        sch = b.decode()
    else:
        sch = None

    sbml_to_neo4j(xml, sch, tag)
