import logging

from fastapi import APIRouter, Response, UploadFile

from ..database import DbDep
from ..models import Graph
from ..neo4jsbml import sbml_from_neo4j, sbml_to_neo4j

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/model", tags=["model"])


@router.get("/")
def models(db: DbDep) -> Graph:
    return db.get_graph()


@router.get("/by-name/{model_name}")
def model_by_name(
    db: DbDep,
    model_name: str,
) -> Graph:
    return db.get_model_by_name(model_name)


@router.get("/by-node")
def model_by_node(
    db: DbDep,
    label: str,
    property: str,
    value: str,
) -> Graph:
    return db.get_model_by_node(label, property, value)


@router.post("/upload")
async def upload(db: DbDep, file: UploadFile) -> None:
    b = await file.read()
    xml = b.decode()

    tag = db.get_max_tag() + 1

    logger.info("Importing SBML, using tag %d", tag)

    sbml_to_neo4j(xml, tag)


@router.get("/download")
async def download(db: DbDep):
    raise NotImplementedError()

    tag = 1
    logger.info("Exporting SBML, using tag %d", tag)

    xml = sbml_from_neo4j(tag)
    return Response(
        content=xml,
        media_type="application/sbml+xml",
        headers={
            "Content-Disposition": "attachment; filename=",
        },
    )
