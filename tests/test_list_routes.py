def test_lists_require_login(client):
    response = client.get("/lists")

    assert response.status_code in (302, 401)
