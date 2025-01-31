from collections.abc import Callable
from functools import wraps
from typing import Any

from prefect.events import emit_event


def emit_event_on_call(
    owner: str | None = None,
    event_name: str = "tool-called",
    extra_resources: dict | None = None,
    extra_payload: dict | None = None,
) -> Callable:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)
            emit_event(
                event=event_name,
                resource={
                    "prefect.resource.id": f"{owner or 'ai'}.tool.{fn.__name__}.{id(fn)}",
                    **(extra_resources or {}),
                },
                payload=dict(result=result, **(extra_payload or {})),
            )
            return result

        return wrapper

    return decorator
