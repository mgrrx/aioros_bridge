import json
from typing import AsyncIterator, Dict, Union

from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request
from starlette.responses import JSONResponse

from aioros import RawMessage
from aioros.abc import Node

from ._conversion import import_msg_class, to_dict


async def subscribe(node: Node, topic_name: str) -> AsyncIterator[Dict]:
    msg_class = None
    async with node.create_subscription(topic_name, RawMessage) as subscription:
        async for msg in subscription:
            msg_class = msg_class or import_msg_class(msg._connection_header["type"])
            real_msg = msg_class()
            real_msg.deserialize(msg.raw)
            yield {"data": json.dumps(to_dict(real_msg))}


async def sse(request: Request) -> Union[EventSourceResponse, JSONResponse]:
    topic_name = request["path"]
    node: Node = request.app.node
    try:
        topic_name = node.resolve_name(topic_name)
    except ValueError:
        return JSONResponse({"detail": f"Invalid topic name {topic_name}"}, 400)
    return EventSourceResponse(subscribe(node, topic_name))
