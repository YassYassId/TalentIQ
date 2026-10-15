import uuid


BASE_URL = "/api/v1/candidates"


def test_create_candidate(client):
    response = client.post(
        BASE_URL,
        json={
            "full_name": "Alice Johnson",
            "email": "alice@example.com",
            "phone": "+212600123456",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == "Alice Johnson"
    assert data["email"] == "alice@example.com"
    assert "id" in data
    assert "created_at" in data


def test_get_candidate(client):
    created = client.post(
        BASE_URL,
        json={"full_name": "Bob Smith"},
    ).json()

    response = client.get(f"{BASE_URL}/{created['id']}")

    assert response.status_code == 200
    assert response.json()["full_name"] == "Bob Smith"


def test_list_candidates(client):
    client.post(
        BASE_URL,
        json={"full_name": "Jane Doe"},
    )

    response = client.get(
        BASE_URL,
        params={"offset": 0, "limit": 10},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_update_candidate(client):
    created = client.post(
        BASE_URL,
        json={
            "full_name": "John Smith",
            "email": "john@example.com",
        },
    ).json()

    response = client.patch(
        f"{BASE_URL}/{created['id']}",
        json={"phone": "+212611111111"},
    )

    assert response.status_code == 200
    assert response.json()["phone"] == "+212611111111"
    assert response.json()["email"] == "john@example.com"


def test_delete_candidate(client):
    created = client.post(
        BASE_URL,
        json={"full_name": "Delete Me"},
    ).json()

    response = client.delete(f"{BASE_URL}/{created['id']}")

    assert response.status_code == 204

    get_response = client.get(
        f"{BASE_URL}/{created['id']}"
    )

    assert get_response.status_code == 404


def test_invalid_email(client):
    response = client.post(
        BASE_URL,
        json={
            "full_name": "Invalid Email",
            "email": "not-an-email",
        },
    )

    assert response.status_code == 422


def test_candidate_not_found(client):
    unknown_id = uuid.uuid4()

    response = client.get(f"{BASE_URL}/{unknown_id}")

    assert response.status_code == 404