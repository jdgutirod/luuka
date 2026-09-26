import pytest


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200


def test_cors_allows_the_frontend_origin(client):
    response = client.options(
        "/accounts/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


@pytest.mark.parametrize("header", ["Idempotency-Key", "Content-Type"])
def test_cors_allows_the_headers_the_frontend_sends(client, header):
    response = client.options(
        "/transactions/transfers",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": header,
        },
    )

    assert response.status_code == 200


def test_cors_rejects_unknown_origins(client):
    response = client.get("/health", headers={"Origin": "https://sitio-malicioso.com"})

    assert "access-control-allow-origin" not in response.headers
