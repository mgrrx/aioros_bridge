import json
from typing import Any, AsyncIterator, Dict, Type

from genpy import Duration, Time
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request

from aioros import RawMessage
from aioros.abc import Message, Node


def import_msg_class(msg: RawMessage) -> Type[Message]:
    module_name, cls_name = msg._connection_header["type"].split("/")
    return getattr(getattr(__import__(module_name + ".msg"), "msg"), cls_name)


def to_dict(msg: Message) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for key in msg.__slots__:
        value = getattr(msg, key)
        if isinstance(value, (Time, Duration)):
            data[key] = dict(secs=value.secs, nsecs=value.nsecs)
        elif isinstance(value, Message):
            data[key] = to_dict(value)
        elif isinstance(value, list):
            if len(value) == 0:
                data[key] = value
            elif isinstance(value[0], (Time, Duration)):
                data[key] = [dict(secs=i.secs, nsecs=i.nsecs) for i in value]
            elif isinstance(value[0], Message):
                data[key] = [to_dict(i) for i in value]
            else:
                data[key] = value
        else:
            data[key] = value
    return data


async def subscribe(node: Node, topic_name: str) -> AsyncIterator[Dict]:
    msg_class = None
    async with node.create_subscription(topic_name, RawMessage) as subscription:
        async for msg in subscription:
            msg_class = msg_class or import_msg_class(msg)
            real_msg = msg_class()
            real_msg.deserialize(msg.raw)
            yield {"data": json.dumps(to_dict(real_msg))}


async def sse(request: Request) -> EventSourceResponse:
    return EventSourceResponse(
        subscribe(
            request.app.state.node,
            "/" + request.path_params["topic_name"],
        )
    )
