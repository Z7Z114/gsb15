"""行为规格验收测试：逐条对应 README.md「行为规格（验收标准）」。

这些用例在未修复的实现上应当失败，修复后全部通过。
"""
import os

from tests.conftest import make_conversation, make_member, make_vegetable


# ---------- A. 音频上传与转写链路 ----------

def test_upload_audio_saves_and_returns_file_info(client):
    member = make_member(client, email="a1@csa.com")
    conv = make_conversation(client, member["id"])

    resp = client.post(
        f"/api/conversations/{conv['id']}/upload-audio",
        files={"audio_file": ("meeting.mp3", b"fake-audio-bytes", "audio/mpeg")},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["filename"] == "meeting.mp3"
    assert data["conversation_id"] == conv["id"]
    assert data["file_path"].endswith("meeting.mp3")
    assert os.path.isfile(data["file_path"])


def test_upload_audio_missing_conversation_returns_404(client):
    resp = client.post(
        "/api/conversations/9999/upload-audio",
        files={"audio_file": ("x.mp3", b"data", "audio/mpeg")},
    )
    assert resp.status_code == 404


def test_upload_audio_persists_path_to_transcript(client):
    member = make_member(client, email="a2@csa.com")
    conv = make_conversation(client, member["id"])

    upload = client.post(
        f"/api/conversations/{conv['id']}/upload-audio",
        files={"audio_file": ("talk.wav", b"wav-bytes", "audio/wav")},
    )
    assert upload.status_code == 200
    file_path = upload.json()["file_path"]

    transcript = client.get(f"/api/conversations/{conv['id']}/transcript").json()
    assert transcript is not None
    assert transcript["audio_file_path"] == file_path

    # 「开始转写」不得再报「对话没有音频文件」即失败
    resp = client.post(f"/api/ai/transcribe/{conv['id']}")
    assert resp.status_code == 200, resp.text


def test_upload_audio_sanitizes_filename(client):
    member = make_member(client, email="a3@csa.com")
    conv = make_conversation(client, member["id"])

    for evil in ["../../evil.mp3", "..\\..\\evil2.mp3", "sub/dir/evil3.mp3"]:
        resp = client.post(
            f"/api/conversations/{conv['id']}/upload-audio",
            files={"audio_file": (evil, b"data", "audio/mpeg")},
        )
        assert resp.status_code == 200, resp.text
        file_path = resp.json()["file_path"]
        assert ".." not in file_path
        assert os.path.dirname(file_path) == "uploads/audio"
        assert os.path.isfile(file_path)


# ---------- B. Transcript 唯一性 ----------

def test_transcript_post_is_idempotent_upsert(client):
    member = make_member(client, email="b1@csa.com")
    conv = make_conversation(client, member["id"])

    first = client.post(
        "/api/conversations/transcript",
        json={"conversation_id": conv["id"], "raw_transcript": "第一版"},
    )
    assert first.status_code == 200
    second = client.post(
        "/api/conversations/transcript",
        json={"conversation_id": conv["id"], "raw_transcript": "第二版"},
    )
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]

    got = client.get(f"/api/conversations/{conv['id']}/transcript").json()
    assert got["id"] == first.json()["id"]
    assert got["raw_transcript"] == "第二版"


# ---------- C. 会员更新校验 ----------

def test_update_member_email_conflict_returns_400_and_keeps_data(client):
    make_member(client, name="甲", email="c1@csa.com")
    other = make_member(client, name="乙", email="c2@csa.com", role="consumer")

    resp = client.put(
        f"/api/members/{other['id']}",
        json={"name": "乙", "email": "c1@csa.com", "role": "consumer"},
    )
    assert resp.status_code == 400, resp.text

    unchanged = client.get(f"/api/members/{other['id']}").json()
    assert unchanged["email"] == "c2@csa.com"


def test_update_member_email_no_conflict_ok(client):
    member = make_member(client, name="丙", email="c3@csa.com")
    resp = client.put(
        f"/api/members/{member['id']}",
        json={"name": "丙", "email": "c3-new@csa.com", "role": "farmer"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == "c3-new@csa.com"


def test_update_missing_member_returns_404(client):
    resp = client.put(
        "/api/members/9999",
        json={"name": "无人", "email": "nobody@csa.com", "role": "farmer"},
    )
    assert resp.status_code == 404


# ---------- D. 蔬菜更新的主键安全 ----------

def test_update_vegetable_body_id_cannot_change_primary_key(client):
    veg = make_vegetable(client, name="番茄", season="summer", share_quota=50)
    other = make_vegetable(client, name="黄瓜", season="summer")

    payload = {
        "id": other["id"],
        "name": "大番茄",
        "season": "autumn",
        "share_quota": 99,
    }
    resp = client.put(f"/api/vegetables/{veg['id']}", json=payload)
    assert resp.status_code == 200, resp.text

    updated = client.get(f"/api/vegetables/{veg['id']}").json()
    assert updated["id"] == veg["id"]
    assert updated["name"] == "大番茄"
    assert updated["season"] == "autumn"
    assert updated["share_quota"] == 99

    untouched = client.get(f"/api/vegetables/{other['id']}").json()
    assert untouched["name"] == "黄瓜"


# ---------- E. 蔬菜删除的关联处理 ----------

def test_delete_vegetable_cascades_calendar_entries(client):
    veg = make_vegetable(client, name="青菜", season="autumn")
    entry = client.post(
        "/api/calendar/",
        json={
            "vegetable_id": veg["id"],
            "activity_type": "planting",
            "activity_date": "2026-08-15",
        },
    )
    assert entry.status_code == 200
    entry_id = entry.json()["id"]

    resp = client.delete(f"/api/vegetables/{veg['id']}")
    assert resp.status_code == 200, resp.text
    assert client.get(f"/api/vegetables/{veg['id']}").status_code == 404

    calendar = client.get("/api/calendar").json()
    assert all(e["id"] != entry_id for e in calendar)
    assert all(e["vegetable_id"] != veg["id"] for e in calendar)


def test_delete_missing_vegetable_returns_404(client):
    assert client.delete("/api/vegetables/9999").status_code == 404


# ---------- F. 查询参数命名 ----------

def test_calendar_filters_accept_camel_and_snake_case(client):
    veg = make_vegetable(client, name="萝卜", season="winter")
    for activity_type, day in [("planting", "2026-03-10"), ("watering", "2026-05-10")]:
        resp = client.post(
            "/api/calendar/",
            json={"vegetable_id": veg["id"], "activity_type": activity_type, "activity_date": day},
        )
        assert resp.status_code == 200

    for params in (
        {"startDate": "2026-04-01", "endDate": "2026-06-01"},
        {"start_date": "2026-04-01", "end_date": "2026-06-01"},
    ):
        result = client.get("/api/calendar", params=params).json()
        assert [e["activity_type"] for e in result] == ["watering"]

    for params in ({"activityType": "planting"}, {"activity_type": "planting"}):
        result = client.get("/api/calendar", params=params).json()
        assert [e["activity_type"] for e in result] == ["planting"]


def test_conversation_filters_accept_camel_and_snake_case(client):
    m1 = make_member(client, email="f1@csa.com")
    m2 = make_member(client, email="f2@csa.com")
    make_conversation(client, m1["id"], title="对话一")
    make_conversation(client, m2["id"], title="对话二")

    for params in ({"memberId": m1["id"]}, {"member_id": m1["id"]}):
        result = client.get("/api/conversations", params=params).json()
        assert len(result) == 1
        assert result[0]["member_id"] == m1["id"]

    closed = client.post(
        "/api/conversations/", json={"member_id": m1["id"], "title": "已关闭", "status": "closed"}
    )
    assert closed.status_code == 200
    result = client.get("/api/conversations", params={"status": "closed"}).json()
    assert len(result) == 1
    assert result[0]["status"] == "closed"


def test_feedback_filters_accept_camel_and_snake_case(client):
    m1 = make_member(client, email="f3@csa.com")
    m2 = make_member(client, email="f4@csa.com")
    for member, ftype in [(m1, "taste"), (m2, "delivery")]:
        resp = client.post(
            "/api/conversations/feedback",
            json={"member_id": member["id"], "feedback_type": ftype, "content": "反馈"},
        )
        assert resp.status_code == 200

    for params in ({"memberId": m1["id"]}, {"member_id": m1["id"]}):
        result = client.get("/api/conversations/feedback/list", params=params).json()
        assert len(result) == 1
        assert result[0]["member_id"] == m1["id"]

    for params in ({"feedbackType": "delivery"}, {"feedback_type": "delivery"}):
        result = client.get("/api/conversations/feedback/list", params=params).json()
        assert len(result) == 1
        assert result[0]["feedback_type"] == "delivery"


def test_summary_filter_accepts_camel_and_snake_case(client):
    assert client.post("/api/ai/generate-planting-intent", json=[]).status_code == 200
    for params in ({"summaryType": "planting_intent"}, {"summary_type": "planting_intent"}):
        result = client.get("/api/ai/summaries", params=params).json()
        assert len(result) >= 1
        assert all(s["summary_type"] == "planting_intent" for s in result)
    for params in ({"summaryType": "meeting_summary"}, {"summary_type": "meeting_summary"}):
        assert client.get("/api/ai/summaries", params=params).json() == []


def test_vegetable_filters_accept_camel_case_and_bool_forms(client):
    make_vegetable(client, name="夏菜", season="summer")
    make_vegetable(client, name="冬菜", season="winter", is_available=False)

    result = client.get("/api/vegetables", params={"season": "summer"}).json()
    assert {v["name"] for v in result} == {"夏菜"}

    for value in ("false", "FALSE", "0"):
        result = client.get("/api/vegetables", params={"availableOnly": value}).json()
        assert {v["name"] for v in result} == {"夏菜", "冬菜"}
    for value in ("true", "TRUE", "1"):
        result = client.get("/api/vegetables", params={"availableOnly": value}).json()
        assert {v["name"] for v in result} == {"夏菜"}
    result = client.get("/api/vegetables", params={"available_only": "false"}).json()
    assert {v["name"] for v in result} == {"夏菜", "冬菜"}


def test_member_filters_accept_camel_case_and_bool_forms(client):
    make_member(client, name="农人A", email="f5@csa.com", role="farmer")
    consumer = make_member(client, name="会员B", email="f6@csa.com", role="consumer")
    client.delete(f"/api/members/{consumer['id']}")

    result = client.get("/api/members", params={"role": "consumer"}).json()
    assert result == []

    for value in ("false", "FALSE", "0"):
        result = client.get("/api/members", params={"activeOnly": value}).json()
        assert {m["name"] for m in result} == {"农人A", "会员B"}
    for value in ("true", "TRUE", "1"):
        result = client.get("/api/members", params={"activeOnly": value}).json()
        assert {m["name"] for m in result} == {"农人A"}
    result = client.get("/api/members", params={"active_only": "false"}).json()
    assert {m["name"] for m in result} == {"农人A", "会员B"}


# ---------- G. AI 接口的请求形状 ----------

def test_generate_recipes_accepts_query_params(client):
    resp = client.post(
        "/api/ai/generate-recipes",
        params=[("vegetables", "番茄"), ("vegetables", "黄瓜"), ("count", "2")],
    )
    assert resp.status_code == 200, resp.text
    assert "recipes" in resp.json()
    assert isinstance(resp.json()["recipes"], list)


def test_generate_recipes_accepts_bracket_array_params(client):
    resp = client.post(
        "/api/ai/generate-recipes",
        params=[("vegetables[]", "番茄"), ("vegetables[]", "黄瓜"), ("count", "2")],
    )
    assert resp.status_code == 200, resp.text
    assert "recipes" in resp.json()


def test_generate_planting_intent_accepts_all_body_shapes(client):
    expected_keys = {
        "next_season_vegetables",
        "share_adjustments",
        "member_preferences",
        "recommendations",
    }
    for body in (
        {"conversationIds": [1, 2]},
        {"conversation_ids": [1, 2]},
        [1, 2],
    ):
        resp = client.post("/api/ai/generate-planting-intent", json=body)
        assert resp.status_code == 200, resp.text
        assert expected_keys <= set(resp.json().keys())
