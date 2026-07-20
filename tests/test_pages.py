from fastapi.testclient import TestClient


def test_landing_renders_product_story(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Start the role" in response.text
    assert "OpenAI Build Week 2026" in response.text


def test_pages_use_origin_relative_static_assets(client: TestClient) -> None:
    response = client.get("/reviewers")
    assert response.status_code == 200
    assert 'href="/static/styles.css"' in response.text
    assert 'src="/static/app.js"' in response.text
    assert "://testserver/static/" not in response.text


def test_journey_renders_real_day_state(client: TestClient) -> None:
    response = client.get("/journey")
    assert response.status_code == 200
    assert "Good morning, Jordan" in response.text
    assert "Make one low-cost ask" in response.text
    assert "Transition coach" in response.text


def test_studio_uses_fictional_european_profiles(client: TestClient) -> None:
    response = client.get("/studio")
    assert response.status_code == 200
    assert "Riga" in response.text
    assert "Berlin" in response.text
    assert "Stockholm" in response.text
    assert "Private journal content is never shown" not in response.text
    assert "Teams see patterns, never private journal entries" in response.text


def test_admin_guide_is_a_separate_studio_section(client: TestClient) -> None:
    response = client.get("/studio/guide")
    assert response.status_code == 200
    assert "Run First 90 with confidence" in response.text
    assert "Know what admins can see" in response.text
    assert "journal or coach text" in response.text
    assert "Create a reviewer admin chat" in response.text
    assert "https://t.me/&lt;bot_username&gt;" in response.text


def test_participant_guide_explains_free_access_and_payment_phase_two(
    client: TestClient,
) -> None:
    response = client.get("/guide")
    assert response.status_code == 200
    assert "Current early access is free" in response.text
    assert "No card. No checkout. No billing data." in response.text
    assert "NEXT · PHASE 2" in response.text
    assert "Hosted secure checkout" in response.text


def test_participant_guide_includes_telegram_onboarding_and_first_days(
    client: TestClient,
) -> None:
    response = client.get("/guide")
    assert response.status_code == 200
    assert "Step 1 of 6" in response.text
    assert "Step 6 of 6" in response.text
    assert "Name the identity shift" in response.text
    assert "day-01-identity-shift.webp" in response.text
    assert "Google re:Work guide to team effectiveness" in response.text


def test_reviewer_guide_is_honest_and_actionable(client: TestClient) -> None:
    response = client.get("/reviewers")
    assert response.status_code == 200
    assert "Test the product, not a slide deck" in response.text
    assert "/preview 1" in response.text
    assert "People Manager" in response.text
    assert "Only People Manager has a complete reviewed journey" in response.text
