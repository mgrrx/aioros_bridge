import json

from genpy import Time
from starlette.applications import Starlette
from starlette.testclient import TestClient


def test_app(app_with_publisher: Starlette) -> None:
    with TestClient(app_with_publisher) as client:

        # Nodes API
        assert client.get("/api/nodes").json() == ["/test_publisher"]
        assert client.get("/api/nodes/test_publisher").json() == {
            "publishing": ["/chatter"],
            "subscribing": [],
            "services": ["/set_bool"],
        }
        assert client.get("/api/nodes/foo").status_code == 400

        # topics API
        assert client.get("/api/topics/").json() == [
            {
                "type": "std_msgs/String",
                "topic": "/chatter",
            }
        ]
        assert client.get("/api/topics/chatter").json() == {
            "type": "std_msgs/String",
            "publishing": ["/test_publisher"],
            "subscribing": [],
        }
        assert client.get("/api/topics/foo").status_code == 400

        assert client.get("/api/params/").json() == []
        assert (
            client.put("/api/params/foo", data=json.dumps({"bar": 1})).status_code
            == 200
        )
        assert client.get("/api/params/foo").json() == {"bar": 1}
        assert client.get("/api/params/").json() == ["/foo/bar"]

        assert client.put("/api/params/foo/bar2", data=json.dumps(2)).status_code == 200

        assert client.get("/api/params/").json() == ["/foo/bar", "/foo/bar2"]
        assert client.delete("/api/params/foo/bar").status_code == 200
        assert client.get("/api/params/").json() == ["/foo/bar2"]

        assert client.delete("/api/params/foo/bar2").status_code == 200
        assert client.get("/api/params/").json() == []

        assert client.get("/api/services/").json() == ["/set_bool"]

        # Time
        now = app_with_publisher.node.get_time()
        api_time = client.get("/api/time").json()
        delta = Time(api_time["secs"], api_time["nsecs"]) - now
        assert delta.to_sec() < 0.1
