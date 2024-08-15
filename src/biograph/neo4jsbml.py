import logging
from urllib.parse import urlparse

import libsbml
from neo4jsbml import arrows, connect, sbml
from pydantic import BaseModel

from . import config
from .database import Config as DbConfig

logger = logging.getLogger(__name__)


class Config(BaseModel):
    schema_path: str

    @classmethod
    def get(cls):
        return config.get(cls, "neo4jsbml")


def sbml_to_neo4j(xml: str, tag: int):
    cfg = Config.get()
    db_cfg = DbConfig.get()

    parsed_uri = urlparse(db_cfg.uri)
    conn = connect.Connect(
        protocol=parsed_uri.scheme,
        url=parsed_uri.hostname,
        port=parsed_uri.port,
        user=db_cfg.username,
        database=db_cfg.database,
        password=db_cfg.password,
    )
    conn.driver.verify_connectivity()

    logger.info("Loading SBML")
    doc = libsbml.readSBMLFromString(xml)
    errors = doc.getNumErrors()
    if errors > 0:
        raise ValueError("SBML parse error")

    sbm = sbml.SbmlToNeo4j(str(tag), document=doc)

    logger.info("Loading schema")
    arr = arrows.Arrows.from_json(cfg.schema_path)

    logging.info("Map schema to data - nodes")
    nod = sbm.format_nodes(nodes=arr.nodes)

    rel = None
    if arr.relationships:
        logging.info("Map schema to data - relationships")
        rel = sbm.format_relationships(relationships=arr.relationships)

    logging.info("Import into neo4j - nodes")
    conn.create_nodes(nodes=nod)

    if rel:
        logging.info("Import into neo4j - relationships")
        conn.create_relationships(relationships=rel)
    else:
        logging.info("No relationships created")


def sbml_from_neo4j(tag: int):
    cfg = Config.get()
    db_cfg = DbConfig.get()

    parsed_uri = urlparse(db_cfg.uri)
    conn = connect.Connect(
        protocol=parsed_uri.scheme,
        url=parsed_uri.hostname,
        port=parsed_uri.port,
        user=db_cfg.username,
        database=db_cfg.database,
        password=db_cfg.password,
    )
    conn.driver.verify_connectivity()

    logging.info("Initialize data")
    sbm = sbml.SbmlFromNeo4j.from_specifications(
        level=3,
        version=2,
        connection=conn,
    )

    logging.info("Load schema")
    arr = arrows.Arrows.from_json(cfg.schema_path, add_id=False)

    logging.info("Filtering schema based on libsbml")
    sbm.annotate(modelisation=arr)

    logging.info("Extracting entities")
    sbm.conciliate_labels()
    sbm.extract_entities()

    logging.info("Writing model")
    data = libsbml.writeSBMLToString(sbm.document)

    return data
