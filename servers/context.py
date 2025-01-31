# /// script
# dependencies = ["lancedb", "openai", "pydantic-settings", "mcp"]
# ///

"""
FastMCP Context Manager
--------------------------------
Simple knowledge base using LanceDB with OpenAI embeddings.
Create domains and add/search knowledge with metadata.

To run this example, create a `.env` file with:
OPENAI_API_KEY=...

---
Run as a goose extension:

    goose session --with-extension "$(cat .env | tr '\n' ' ') uv run context.py"
"""

from pathlib import Path

import lancedb
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector
from mcp.server.fastmcp import FastMCP
from pydantic import model_validator
from pydantic_core import from_json, to_json
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LANCEDB_")

    @model_validator(mode="before")
    def ensure_db_file(cls, values):
        if not (p := Path(".lancedb")).exists():
            p.mkdir(exist_ok=True)
        return values


# Get OpenAI embeddings
embeddings = get_registry().get("openai").create()


class Document(LanceModel):
    """Base schema for all knowledge domains"""

    text: str = embeddings.SourceField()
    vector: Vector(1536) = embeddings.VectorField()  # type: ignore[reportInvalidTypeform]
    source: str | None = None
    metadata: str | None = None  # JSON string for Arrow compatibility


mcp = FastMCP("Context Manager")
db = lancedb.connect(".lancedb")


@mcp.tool(name="create_domain", description="Create a new knowledge domain")
def create_domain(name: str) -> str:
    """Create a new domain (table) for storing knowledge"""
    try:
        db.create_table(name, schema=Document, mode="overwrite")
        return f"Created domain '{name}' successfully"
    except Exception as e:
        return f"Failed to create domain: {str(e)}"


@mcp.tool(name="delete_domain", description="Delete a domain")
def delete_domain(name: str) -> str:
    """Delete a domain (table) for storing knowledge"""
    try:
        db.drop_table(name)
        return f"Deleted domain '{name}' successfully"
    except Exception as e:
        return f"Failed to delete domain: {str(e)}"


@mcp.tool(name="list_domains", description="List all knowledge domains")
def list_domains() -> list[str]:
    """List all available domains"""
    return list(db.table_names())


@mcp.tool(name="add_knowledge", description="Add knowledge to a domain")
def add_knowledge(
    domain: str,
    text: str,
    source: str | None = None,
    metadata: dict | None = None,
) -> str:
    """Add a piece of knowledge to a domain"""
    try:
        table = db.open_table(domain)
        data = {
            "text": text,
            "source": source,
            "metadata": to_json(metadata).decode("utf-8") if metadata else None,
        }
        table.add([data])
        return f"Added knowledge to domain '{domain}' successfully"
    except Exception as e:
        return f"Failed to add knowledge: {str(e)}"


@mcp.tool(name="search", description="Search for knowledge across domains")
def search(query: str, domain: str | None = None, limit: int = 5) -> list[dict]:
    """Search for knowledge using semantic search"""
    results = []
    domains = [domain] if domain else db.table_names()

    for d in domains:
        try:
            table = db.open_table(d)
            search_results = (
                table.search(query)
                .select(["text", "source", "metadata", "_distance"])
                .limit(limit)
                .to_list()
            )
            for r in search_results:
                if r.get("metadata"):
                    r["metadata"] = from_json(r["metadata"])
                r["domain"] = d
                results.append(r)
        except Exception as e:
            results.append({"error": f"Failed to search domain '{d}': {str(e)}"})

    return results


if __name__ == "__main__":
    mcp.run()
