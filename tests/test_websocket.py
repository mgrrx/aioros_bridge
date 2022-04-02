from starlette.applications import Starlette
from starlette.testclient import TestClient


def test_app(app_with_publisher: Starlette) -> None:
    with TestClient(app_with_publisher) as client, client.websocket_connect(
        "/ws"
    ) as websocket:
        websocket.send_json(
            {
                "op": "subscribe",
                "topic": "/chatter",
                "type": "std_msgs/String",
            }
        )
        data = websocket.receive_json()
        assert data == {
            "op": "publish",
            "topic": "/chatter",
            "msg": {"data": "Message 1"},
        }
        websocket.send_json(
            {
                "op": "unsubscribe",
                "topic": "/chatter",
            }
        )
        websocket.close()
