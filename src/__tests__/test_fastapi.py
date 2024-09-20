import pytest
from fastapi.testclient import TestClient
from neo4j import GraphDatabase
import urllib.parse
import subprocess

# Import actual main module from the source code
from . import main

# URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
URI = "neo4j://localhost:7687"
AUTH = ("neoj4", "12345678")


client = TestClient(main.api)


@pytest.fixture()
def query():
    def inner(q: str):
        q = urllib.parse.quote_plus(q)
        res = client.get(f"query/raw?q={q}")
        assert res.status_code == 200, res
        return res.json()

    return inner


@pytest.fixture(scope="session")
def database_fixure():
    ref = client.delete("/model/all")
    assert ref.status_code == 200


@pytest.fixture(scope="session")
def model(database_fixure):
    with open("./tests/models/Malkov2020.xml", "rb") as file:
        response = client.post("/model/upload", files={"file": file})
        assert response.status_code == 200, response.json()


def test_schema():
    with open("./config/schema.json", "rb") as file:
        response = client.post("/model/upload-schema", files={"file": file})

        assert response.status_code == 200, response.json()


def test_query(query, model):
    data = query("MATCH (n) RETURN n")
    assert len(data) == 23


def test_query_by_node(model):
    response = client.get(
        "/model/by-node?label=Reaction&property=name&value=Exposed_To_Infected"
    )
    assert response.status_code == 200, response.json()
    obj = response.json()
    assert len(obj) > 0


def test_fetch(model):
    response = client.get("/model/all")
    assert response.status_code == 200, response.json()
    obj = response.json()
    print(obj["nodes"])
    assert len(obj["nodes"]) == 23


def test_upload(model):
    with open("./tests/models/Hou2020.xml", "rb") as file:
        response = client.post("/model/upload", files={"file": file})

        assert response.status_code == 200, response.json()


def test_bad_upload(model):
    with open("./src/biograph/config.py", "rb") as file:
        response = client.post("/model/upload", files={"file": file})

        assert response.status_code == 500, response.json()
