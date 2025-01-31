# /// script
# dependencies = ["pydantic-settings", "httpx", "mcp", "geese@git+https://github.com/zzstoatzz/geese.git"]
# ///

"""
FastMCP Text Me Server
--------------------------------
This defines a simple FastMCP server that sends a text message to a phone number via https://surgemsg.com/.
To run this example, create a `.env` file with the following values:
SURGE_API_KEY=...
SURGE_ACCOUNT_ID=...
SURGE_MY_PHONE_NUMBER=...
SURGE_MY_FIRST_NAME=...
SURGE_MY_LAST_NAME=...
Visit https://surgemsg.com/ and click "Get Started" to obtain these values.

---
Run this as a goose extension:

```bash
goose session --with-extension "$(cat .env | tr '\n' ' ') uv run sms.py"
```
"""

from typing import Annotated

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BeforeValidator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from geese._decorators import emit_event_on_call


class SurgeSettings(BaseSettings):
    model_config: SettingsConfigDict = SettingsConfigDict(
        env_prefix="SURGE_", extra="ignore"
    )

    api_key: str = Field(default=...)
    account_id: str = Field(default=...)
    my_phone_number: Annotated[
        str, BeforeValidator(lambda v: "+" + v if not v.startswith("+") else v)
    ] = Field(default=...)
    my_first_name: str = Field(default=...)
    my_last_name: str = Field(default=...)


mcp = FastMCP("SMS-Server")
surge_settings = SurgeSettings()


@mcp.tool(name="textme", description="Send a text message to me")
@emit_event_on_call(owner=mcp.name, event_name="sms-sent")
def text_me(text_content: str) -> str:
    """Send a text message to the user that you operate on behalf of."""
    with httpx.Client() as client:
        response = client.post(
            "https://api.surgemsg.com/messages",
            headers={
                "Authorization": f"Bearer {surge_settings.api_key}",
                "Surge-Account": surge_settings.account_id,
                "Content-Type": "application/json",
            },
            json={
                "body": text_content,
                "conversation": {
                    "contact": {
                        "first_name": surge_settings.my_first_name,
                        "last_name": surge_settings.my_last_name,
                        "phone_number": surge_settings.my_phone_number,
                    }
                },
            },
        )
        response.raise_for_status()
        return f"Message sent: {text_content}"


if __name__ == "__main__":
    mcp.run()
