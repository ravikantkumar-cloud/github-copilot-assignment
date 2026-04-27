import pytest
from fastapi.testclient import TestClient
from app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before each test."""
    original = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    activities.clear()
    activities.update(original)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_get_activities(client):
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Gym Class" in data


def test_signup_success(client):
    response = client.post("/activities/Chess Club/signup?email=alice@mergington.edu")
    assert response.status_code == 200
    assert "alice@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_activity_not_found(client):
    response = client.post("/activities/Nonexistent/signup?email=alice@mergington.edu")
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate(client):
    response = client.post("/activities/Chess Club/signup?email=michael@mergington.edu")
    assert response.status_code == 400
    assert response.json()["detail"] == "Already signed up for this activity"


def test_signup_activity_full(client):
    activities["Chess Club"]["max_participants"] = 2  # Already has 2 participants
    response = client.post("/activities/Chess Club/signup?email=alice@mergington.edu")
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_signup_invalid_email(client):
    response = client.post("/activities/Chess Club/signup?email=not-an-email")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email address"


def test_signup_wrong_domain(client):
    response = client.post("/activities/Chess Club/signup?email=alice@gmail.com")
    assert response.status_code == 400
    assert response.json()["detail"] == "Email must be a @mergington.edu address"


def test_root_redirects(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert "/static/index.html" in response.headers["location"]
