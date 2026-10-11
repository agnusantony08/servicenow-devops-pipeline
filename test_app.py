from app import app


def client():
    return app.test_client()


def test_home_returns_message():
    response = client().get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert "message" in data
    assert "host" in data


def test_health_endpoint_is_ok():
    response = client().get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_unknown_route_returns_404():
    response = client().get("/does-not-exist")
    assert response.status_code == 404
