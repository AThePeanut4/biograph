import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .routes import merge as merge_routes
from .routes import model as model_routes
from .routes import node as node_routes
from .routes import query as query_routes
from .routes import relationship as relationship_routes

logger = logging.getLogger(__name__)


api = FastAPI()

api.add_middleware(GZipMiddleware)
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


api.include_router(model_routes.router)
api.include_router(node_routes.router)
api.include_router(relationship_routes.router)
api.include_router(merge_routes.router)
api.include_router(query_routes.router)
