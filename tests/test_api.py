from fastapi.testclient import TestClient


def test_live_and_ready(client: TestClient) -> None:
    assert client.get("/health/live").json()["status"] == "ok"
    assert client.get("/health/ready").json() == {"status": "ready"}


def test_demo_state_is_day_18_with_three_touchpoints(client: TestClient) -> None:
    payload = client.get("/api/v1/demo/state").json()
    assert payload["participant"]["day"] == 18
    assert payload["participant"]["city"] == "Riga"
    assert [item["touchpoint"] for item in payload["capsules"]] == [
        "focus",
        "action",
        "reflection",
    ]
    assert payload["capsules"][0]["completed"] is True
    assert payload["capsules"][1]["current"] is True


def test_complete_current_touchpoint(client: TestClient) -> None:
    state = client.get("/api/v1/demo/state").json()
    action = next(item for item in state["capsules"] if item["current"])
    response = client.post(f"/api/v1/demo/capsules/{action['id']}/complete")
    assert response.status_code == 200
    assert response.json()["participant"]["touchpoint"] == "reflection"


def test_mood_validation_and_save(client: TestClient) -> None:
    assert client.post("/api/v1/demo/mood", json={"score": 0}).status_code == 422
    response = client.post("/api/v1/demo/mood", json={"score": 5})
    assert response.status_code == 200
    assert response.json()["moods"][-1] == {"day": 18, "score": 5}


def test_private_journal_never_appears_in_studio_payload(client: TestClient) -> None:
    private_text = "My private reflection must stay out of team analytics."
    response = client.post("/api/v1/demo/journal", json={"answer": private_text})
    assert response.status_code == 200
    studio = client.get("/api/v1/studio/overview")
    assert private_text not in studio.text


def test_reset_restores_day_18(client: TestClient) -> None:
    state = client.get("/api/v1/demo/state").json()
    action = next(item for item in state["capsules"] if item["current"])
    client.post(f"/api/v1/demo/capsules/{action['id']}/complete")
    reset = client.post("/api/v1/demo/reset")
    assert reset.status_code == 200
    assert reset.json()["participant"]["day"] == 18
    assert reset.json()["participant"]["touchpoint"] == "action"


def test_european_city_reference(client: TestClient) -> None:
    cities = client.get("/api/v1/reference/cities").json()
    assert len(cities) == 16
    assert {city["name"] for city in cities} >= {"Riga", "Berlin", "Paris", "Lisbon"}
    assert all(city["timezone"].startswith("Europe/") for city in cities)
