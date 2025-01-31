# /// script
# dependencies = ["httpx", "trafilatura", "mcp"]
# ///

"""
Fetch a Wikipedia article at the provided URL, parse its main content,
convert it to Markdown, and return the resulting text.


---
Run as a goose extension:

    goose session --with-extension 'uv run wiki.py'
"""

import httpx
import trafilatura
from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS, ErrorData

mcp = FastMCP("Wiki-Fetcher")


@mcp.tool()
def read_wikipedia_article(url: str) -> str:
    """
    Fetch a Wikipedia article at the provided URL, parse its main content,
    convert it to Markdown, and return the resulting text.

    Usage:
        read_wikipedia_article("https://en.wikipedia.org/wiki/Python_(programming_language)")
    """
    try:
        if (response := httpx.get(url, timeout=10)).status_code != 200:
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"Failed to retrieve the article. HTTP status code: {response.status_code}",
                )
            )
        if not (downloaded := trafilatura.fetch_url(url)):
            raise McpError(
                ErrorData(
                    code=INVALID_PARAMS,
                    message="Could not download the content from the provided Wikipedia URL.",
                )
            )

        if not (
            markdown_text := trafilatura.extract(downloaded, output_format="markdown")
        ):
            raise McpError(
                ErrorData(
                    code=INVALID_PARAMS,
                    message="Could not extract the main content from the provided Wikipedia URL.",
                )
            )
        return markdown_text

    except ValueError as e:
        raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e))) from e
    except httpx.RequestError as e:
        raise McpError(
            ErrorData(code=INTERNAL_ERROR, message=f"Request error: {str(e)}")
        ) from e
    except Exception as e:
        raise McpError(
            ErrorData(code=INTERNAL_ERROR, message=f"Unexpected error: {str(e)}")
        ) from e


if __name__ == "__main__":
    mcp.run()
