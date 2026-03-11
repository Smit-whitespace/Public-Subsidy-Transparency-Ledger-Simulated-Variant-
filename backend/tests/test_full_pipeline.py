from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def login():

    res = client.post(
        "/auth/login",
        data={
            "username": "super_admin",
            "password": "123456"
        }
    )

    assert res.status_code == 200

    token = res.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def test_full_subsidy_pipeline():

    headers = login()

    subsidy_payload = {
        "title": "Pipeline Test Subsidy",
        "recipient": "Education Board",
        "sector": "education",
        "total_allocation": "1000000",
        "currency": "INR",
        "status": "active",
        "is_active": True
    }

    res = client.post("/subsidies/", json=subsidy_payload, headers=headers)

    assert res.status_code in [200, 201]

    subsidy = res.json()
    subsidy_id = subsidy["id"]

    disb_payload = {
        "subsidy_id": subsidy_id,
        "amount": "200000",
        "currency": "INR",
        "reference": "PIPELINE-TEST"
    }

    res = client.post("/disbursements/", json=disb_payload, headers=headers)

    assert res.status_code in [200, 201]