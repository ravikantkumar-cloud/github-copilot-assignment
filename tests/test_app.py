"""
Backend tests for Mergington High School API

Uses pytest with FastAPI TestClient and the AAA (Arrange-Act-Assert) pattern.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities database before each test."""
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
        },
        "Art Club": {
            "description": "Explore painting, drawing, and other visual arts",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": ["lisa@mergington.edu"]
        }
    }
    activities.clear()
    activities.update(original)
    yield


@pytest.fixture
def client():
    return TestClient(app)


# ── GET / ────────────────────────────────────────────────────────────────

class TestRootRedirect:
    def test_root_redirects_to_index(self, client):
        # Arrange — nothing extra needed

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


# ── GET /activities ──────────────────────────────────────────────────────

class TestGetActivities:
    def test_returns_all_activities(self, client):
        # Arrange — activities reset by fixture

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert "Art Club" in data

    def test_activity_has_expected_fields(self, client):
        # Arrange
        expected_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for name, details in data.items():
            assert set(details.keys()) == expected_fields, f"{name} missing fields"

    def test_activity_participants_are_lists(self, client):
        # Arrange — default data

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for name, details in data.items():
            assert isinstance(details["participants"], list)


# ── POST /activities/{name}/signup ───────────────────────────────────────

class TestSignup:
    def test_signup_success(self, client):
        # Arrange
        email = "alice@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 200
        assert email in activities[activity]["participants"]

    def test_signup_invalid_email_format(self, client):
        # Arrange
        bad_email = "not-an-email"

        # Act
        response = client.post(f"/activities/Chess Club/signup?email={bad_email}")

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid email address"

    def test_signup_wrong_domain(self, client):
        # Arrange
        email = "alice@gmail.com"

        # Act
        response = client.post(f"/activities/Chess Club/signup?email={email}")

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Email must be a @mergington.edu address"

    def test_signup_nonexistent_activity(self, client):
        # Arrange
        email = "alice@mergington.edu"

        # Act
        response = client.post(f"/activities/Underwater Basket Weaving/signup?email={email}")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate(self, client):
        # Arrange — michael is already in Chess Club
        email = "michael@mergington.edu"

        # Act
        response = client.post(f"/activities/Chess Club/signup?email={email}")

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Already signed up for this activity"

    def test_signup_activity_full(self, client):
        # Arrange — shrink max to current count so it's full
        activities["Art Club"]["max_participants"] = 1

        # Act
        response = client.post(
            "/activities/Art Club/signup?email=newstudent@mergington.edu"
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Activity is full"


# ── DELETE /activities/{name}/unregister ─────────────────────────────────

class TestUnregister:
    def test_unregister_success(self, client):
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.delete(f"/activities/{activity}/unregister?email={email}")

        # Assert
        assert response.status_code == 200
        assert email not in activities[activity]["participants"]

    def test_unregister_nonexistent_activity(self, client):
        # Arrange
        email = "alice@mergington.edu"

        # Act
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_registered(self, client):
        # Arrange — alice is not in Chess Club
        email = "alice@mergington.edu"

        # Act
        response = client.delete(f"/activities/Chess Club/unregister?email={email}")

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not registered for this activity"
