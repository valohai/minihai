def test_smoke(client):
    assert client.get('/').text
