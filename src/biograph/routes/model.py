import logging

from fastapi import APIRouter, UploadFile

from .. import database
from ..api_models import Graph
from ..neo4jsbml import Config as Neo4jSbmlConfig
from ..neo4jsbml import sbml_to_neo4j

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/model", tags=["models"])


@router.get("/all")
def models(db: database.DbDep) -> Graph:
    with db.session() as session:
        g = database.get_graph(session)
    return Graph.from_graph(g)


@router.get("/by-id/{model_uuid}")
def model_by_uuid(
    db: database.DbDep,
    model_uuid: str,
) -> Graph:
    with db.session() as session:
        g = database.get_model_by_uuid(session, model_uuid)
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


@router.get("/by-node-id/{node_uuid}")
def model_by_node_uuid(db: database.DbDep, node_uuid: str) -> Graph:
    with db.session() as session:
        g = database.get_model_by_node_uuid(session, node_uuid)
    return Graph.from_graph(g)


@router.post("/upload")
async def upload_sbml(file: UploadFile, arrows_json: UploadFile | None = None) -> None:
    b = await file.read()
    xml = b.decode()

    logger.info("Importing SBML")

    if arrows_json is not None:
        b = await arrows_json.read()
        schema = b.decode()
    else:
        schema = None

    sbml_to_neo4j(xml, schema)


@router.post("/upload-schema")
async def upload_schema(file: UploadFile) -> None:
    cfg = Neo4jSbmlConfig.get()

    b = await file.read()
    json = b.decode()

    logger.info("Updating schema")

    with open(cfg.schema_path, "w") as f:
        f.write(json)
