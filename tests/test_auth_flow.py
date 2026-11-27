def test_json_login_creates_http_only_session_cookie_and_dashboard_session(client):
    registration = client.post(
        "/api/auth/register",
        json={
            "full_name": "Session Test User",
            "email": "session-test@example.com",
            "password": "Session1234",
            "course": "Test Course",
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"email": "session-test@example.com", "password": "Session1234"},
    )

    assert login.status_code == 200
    assert login.json()["access_token"]
    assert login.cookies.get("access_token")
    assert "httponly" in login.headers["set-cookie"].lower()

    dashboard = client.get("/dashboard", follow_redirects=False)
    assert dashboard.status_code == 200


def test_more_navigation_redirects_to_settings(client):
    response = client.get("/more", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/settings"


def test_authenticated_ai_tutor_page_loads(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Tutor Page User",
            "email": "tutor-page@example.com",
            "password": "TutorPage1234",
            "course": "Test Course",
        },
    )
    login = client.post(
        "/api/auth/login",
        json={"email": "tutor-page@example.com", "password": "TutorPage1234"},
    )
    assert login.status_code == 200

    response = client.get("/ai-tutor")

    assert response.status_code == 200
    assert "AI Learning Assistant" in response.text


def test_forgot_password_returns_generic_response(client):
    response = client.post(
        "/api/auth/forgot-password",
        json={"email": "not-registered@example.com"},
    )

    assert response.status_code == 200
    assert "If that email is registered" in response.json()["message"]


def test_reset_password_rejects_invalid_token(client):
    response = client.post(
        "/api/auth/reset-password",
        json={"token": "invalid", "password": "NewPassword123"},
    )

    assert response.status_code == 400


def test_google_login_start_reports_missing_configuration(client, monkeypatch):
    monkeypatch.setattr("app.routers.auth.settings.GOOGLE_CLIENT_ID", "")
    monkeypatch.setattr("app.routers.auth.settings.GOOGLE_CLIENT_SECRET", "")
    response = client.get("/api/auth/google/start", follow_redirects=False)

    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()