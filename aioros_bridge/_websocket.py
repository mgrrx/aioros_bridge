from dataclasses import dataclass, field
from typing import Any, Callable, Dict, cast

import anyio
from anyio.abc import TaskGroup
from starlette.websockets import WebSocket

from ._conversion import import_msg_class, to_dict

Command = Dict[str, Any]


@dataclass
class Client:
    websocket: WebSocket
    task_group: TaskGroup
    subscriptions: Dict[str, anyio.CancelScope] = field(default_factory=dict)


async def rosbridge(websocket: WebSocket) -> None:
    async with anyio.create_task_group() as task_group:
        client = Client(websocket, task_group)
        await client.websocket.accept()
        async for cmd in client.websocket.iter_json():
            cmd = cast(Command, cmd)
            if handler := HANDLERS.get(cmd["op"]):
                handler(client, cmd)
        task_group.cancel_scope.cancel()


def handle_subscribe(client: Client, cmd: Command) -> None:
    if cmd["topic"] in client.subscriptions:
        # already subscribed
        return
    cancel_scope = anyio.CancelScope()
    client.subscriptions[cmd["topic"]] = cancel_scope
    client.task_group.start_soon(subscribe, client, cancel_scope, cmd)


def handle_unsubscribe(client: Client, cmd: Command) -> None:
    if cmd["topic"] in client.subscriptions:
        client.subscriptions[cmd["topic"]].cancel()
        del client.subscriptions[cmd["topic"]]


async def subscribe(
    client: Client,
    cancel_scope: anyio.CancelScope,
    cmd: Command,
) -> None:
    msg_class = import_msg_class(cmd["type"])
    with cancel_scope:
        async with client.websocket.app.node.create_subscription(
            cmd["topic"], msg_class
        ) as subscription:
            async for message in subscription:
                with anyio.CancelScope(shield=True):
                    await client.websocket.send_json(
                        dict(
                            op="publish",
                            topic=cmd["topic"],
                            msg=to_dict(message),
                        )
                    )


HANDLERS: Dict[str, Callable[[Client, Command], None]] = {
    "subscribe": handle_subscribe,
    "unsubscribe": handle_unsubscribe,
}
