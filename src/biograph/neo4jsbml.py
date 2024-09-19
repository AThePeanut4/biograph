import logging
from typing import cast
from urllib.parse import urlparse
from tempfile import NamedTemporaryFile
import uuid

import libsbml
import neo4j
from neo4jsbml import arrows, connect, sbml
from pydantic import BaseModel

from . import config, database

logger = logging.getLogger(__name__)


class Config(BaseModel):
    schema_path: str

    @classmethod
    def get(cls):
        return config.get(cls, "neo4jsbml")


def sbml_to_neo4j(xml: str, schema: str | None):
    cfg = Config.get()
    db_cfg = database.Config.get()

    parsed_uri = urlparse(db_cfg.uri)
    conn = connect.Connect(
        protocol=parsed_uri.scheme,
        url=parsed_uri.hostname,
        port=parsed_uri.port,
        user=db_cfg.username,
        database=db_cfg.database,
        password=db_cfg.password,
    )

    driver = cast(neo4j.Driver, conn.driver)
    driver.verify_connectivity()

    logger.info("Loading SBML")
    doc = libsbml.readSBMLFromString(xml)
    errors = doc.getNumErrors()
    if errors > 0:
        raise ValueError("SBML parse error")

    tag = str(uuid.uuid4())

    sbm = sbml.SbmlToNeo4j(tag, document=doc)

    logger.info("Loading schema")
    if schema is not None:
        # need a tempfile because neo4jsbml needs a file name
        with NamedTemporaryFile("w+") as f:
            f.write(schema)
            arr = arrows.Arrows.from_json(f.name)
    else:
        arr = arrows.Arrows.from_json(cfg.schema_path)

    logging.info("Map schema to data - nodes")
    nod = sbm.format_nodes(nodes=arr.nodes)

    rel = None
    if arr.relationships:
        logging.info("Map schema to data - relationships")
        rel = sbm.format_relationships(relationships=arr.relationships)

    try:
        logging.info("Import into neo4j - nodes")
        conn.create_nodes(nodes=nod)

        if rel:
            logging.info("Import into neo4j - relationships")
            conn.create_relationships(relationships=rel)
        else:
            logging.info("No relationships created")

        with driver.session(default_access_mode=neo4j.WRITE_ACCESS) as session:
            database.delete_dangling_nodes_by_tag(session, tag)
            database.assign_uuids_by_tag(session, tag)
            database.remove_tag(session, tag)
    except Exception as e:
        logging.error("Error importing sbml into neo4j: %s", e)
        with driver.session(default_access_mode=neo4j.WRITE_ACCESS) as session:
            database.delete_all_by_tag(session, tag)
