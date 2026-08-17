from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


def test_system_messages_crud_and_active_flow():
    # 1. Create a system message via admin endpoint
    create_payload = {
        "title": "Road Closure Alert",
        "body": "National Road 6 undergoing maintenance. Expect minor delays.",
        "target_role": "all",
        "message_type": "warning",
        "is_active": True,
        "is_pinned": True,
        "broadcast_to_notifications": False,
    }
    resp = client.post("/v1/api/travel/admin/messages", json=create_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["title"] == "Road Closure Alert"
    assert data["message_type"] == "warning"
    assert data["is_pinned"] is True
    msg_id = data["id"]

    # 2. List admin messages
    list_resp = client.get("/v1/api/travel/admin/messages")
    assert list_resp.status_code == 200
    messages = list_resp.json()
    assert any(m["id"] == msg_id for m in messages)

    # 3. Get active system messages from travel API for driver role
    active_resp = client.get("/v1/api/travel/messages/active?role=driver")
    assert active_resp.status_code == 200
    active_msgs = active_resp.json()["messages"]
    assert len(active_msgs) >= 1
    assert active_msgs[0]["id"] == msg_id

    # 4. Toggle active state
    toggle_resp = client.post(f"/v1/api/travel/admin/messages/{msg_id}/toggle-active")
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["is_active"] is False

    # Verify deactivated message no longer returns in active messages
    active_resp2 = client.get("/v1/api/travel/messages/active?role=driver")
    assert active_resp2.status_code == 200
    active_msgs2 = active_resp2.json()["messages"]
    assert not any(m["id"] == msg_id for m in active_msgs2)

    # 5. Delete system message
    del_resp = client.delete(f"/v1/api/travel/admin/messages/{msg_id}")
    assert del_resp.status_code == 204
