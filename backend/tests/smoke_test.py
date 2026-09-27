"""顺利路径冒烟测试：在初始快照上必须全部通过。

这些用例只覆盖正常使用场景，用来保证「任务不是靠删测试通过」的底线。
验收标准以 README.md 的「行为规格（验收标准）」为准。
"""
from tests.conftest import make_conversation, make_member, make_vegetable


def test_member_crud_happy_path(client):
    member = make_member(client, name="王会员", email="wang@csa.com", role="consumer")

    assert member["name"] == "王会员"
    assert client.get(f"/api/members/{member['id']}").status_code == 200
    assert any(m["id"] == member["id"] for m in client.get("/api/members").json())


def test_vegetable_crud_happy_path(client):
    veg = make_vegetable(client, name="黄瓜", season="summer", share_quota=80)

    assert veg["share_quota"] == 80
    listing = client.get("/api/vegetables").json()
    assert any(v["id"] == veg["id"] for v in listing)
    assert client.get(f"/api/vegetables/{veg['id']}").json()["name"] == "黄瓜"


def test_missing_resources_return_404(client):
    assert client.get("/api/members/9999").status_code == 404
    assert client.get("/api/vegetables/9999").status_code == 404
    assert client.get("/api/conversations/9999").status_code == 404


def test_conversation_message_flow(client):
    member = make_member(client, name="李消费者", email="li@csa.com", role="consumer")
    conv = make_conversation(client, member["id"], title="口味讨论")

    resp = client.post(
        "/api/conversations/messages",
        json={"conversation_id": conv["id"], "sender_role": "consumer", "content": "番茄很甜"},
    )
    assert resp.status_code == 200

    messages = client.get(f"/api/conversations/{conv['id']}/messages").json()
    assert [m["content"] for m in messages] == ["番茄很甜"]


def test_calendar_entry_happy_path(client):
    veg = make_vegetable(client, name="青菜", season="autumn")
    resp = client.post(
        "/api/calendar/",
        json={
            "vegetable_id": veg["id"],
            "activity_type": "planting",
            "activity_date": "2026-08-15",
            "description": "播种青菜",
        },
    )
    assert resp.status_code == 200
    entry_id = resp.json()["id"]

    toggled = client.patch(f"/api/calendar/{entry_id}/toggle")
    assert toggled.status_code == 200
    assert toggled.json()["completed"] is True


def test_feedback_happy_path(client):
    member = make_member(client, name="赵会员", email="zhao@csa.com", role="consumer")
    resp = client.post(
        "/api/conversations/feedback",
        json={
            "member_id": member["id"],
            "feedback_type": "taste",
            "content": "希望多一些叶菜",
            "rating": 5,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["feedback_type"] == "taste"


def test_offline_ai_endpoints_return_200(client):
    # 未配置任何 Key 时，AI 接口仍要可用（离线分支）。
    assert client.post("/api/ai/generate-planting-intent", json=[]).status_code == 200
    assert client.get("/api/ai/recipes").status_code == 200
    assert client.get("/api/ai/summaries").status_code == 200


def test_offline_email_reports_failure_without_crashing(client):
    # 未配置 SMTP 时邮件发送应返回 5xx 业务错误而不是崩溃；前端据此提示。
    make_member(client, name="钱会员", email="qian@csa.com", role="consumer")
    resp = client.post(
        "/api/email/send",
        json={"to_emails": ["qian@csa.com"], "subject": "标题", "content": "正文"},
    )
    assert resp.status_code == 500
    assert "detail" in resp.json()


def test_root_and_openapi(client):
    assert client.get("/").status_code == 200
    assert client.get("/openapi.json").status_code == 200
