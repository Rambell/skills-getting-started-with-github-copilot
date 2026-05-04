"""
Tests for the Mergington High School Activities API

Tests cover all endpoints with success and error cases using the AAA pattern:
- Arrange: Set up test data and state
- Act: Execute the operation being tested
- Assert: Verify the expected outcome
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app
import copy

# Original activities data for resetting
ORIGINAL_ACTIVITIES = {
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


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Reset activities to original state before and after each test.
    This ensures test isolation and prevents test interference.
    """
    from src import app as app_module
    
    # Arrange: Reset to original state
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
    
    yield
    
    # Cleanup: Reset after test
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# ==============================================================================
# GET / - Root Redirect Tests
# ==============================================================================

def test_root_redirect(client):
    """
    Test that GET / redirects to /static/index.html
    
    AAA:
    - Arrange: Client is ready
    - Act: Send GET request to root
    - Assert: Response redirects to /static/index.html
    """
    # Act
    response = client.get("/", follow_redirects=False)
    
    # Assert
    assert response.status_code == 307
    assert "/static/index.html" in response.headers["location"]


# ==============================================================================
# GET /activities - Get All Activities Tests
# ==============================================================================

def test_get_activities_returns_all_activities(client):
    """
    Test that GET /activities returns all available activities
    
    AAA:
    - Arrange: Activities are preloaded in memory
    - Act: Send GET request to /activities
    - Assert: Response contains all activities with correct structure
    """
    # Act
    response = client.get("/activities")
    activities = response.json()
    
    # Assert
    assert response.status_code == 200
    assert len(activities) == 3
    assert "Chess Club" in activities
    assert "Programming Class" in activities
    assert "Gym Class" in activities


def test_get_activities_includes_participant_details(client):
    """
    Test that activity data includes all required fields
    
    AAA:
    - Arrange: Activities are preloaded in memory
    - Act: Send GET request to /activities
    - Assert: Each activity has description, schedule, max_participants, and participants
    """
    # Act
    response = client.get("/activities")
    activities = response.json()
    
    # Assert
    chess_club = activities["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert chess_club["max_participants"] == 12
    assert len(chess_club["participants"]) == 2


# ==============================================================================
# POST /activities/{activity_name}/signup - Signup Tests
# ==============================================================================

def test_signup_success(client):
    """
    Test successful signup for a valid activity with new email
    
    AAA:
    - Arrange: "Chess Club" exists, "newstudent@mergington.edu" not signed up
    - Act: Send POST request to signup endpoint
    - Assert: Participant is added and success message returned
    """
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}",
        headers={"Content-Type": "application/json"}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    
    # Verify participant was added
    activities_response = client.get("/activities")
    assert email in activities_response.json()[activity_name]["participants"]


def test_signup_duplicate_returns_error(client):
    """
    Test that signup fails when student is already registered
    
    AAA:
    - Arrange: "michael@mergington.edu" is already in Chess Club
    - Act: Send POST request to signup same email again
    - Assert: Returns 400 error with appropriate message
    """
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Already signed up
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}",
        headers={"Content-Type": "application/json"}
    )
    
    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_signup_invalid_activity_returns_404(client):
    """
    Test that signup fails with non-existent activity
    
    AAA:
    - Arrange: "Fake Activity" does not exist
    - Act: Send POST request for non-existent activity
    - Assert: Returns 404 error
    """
    # Arrange
    activity_name = "Fake Activity"
    email = "student@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}",
        headers={"Content-Type": "application/json"}
    )
    
    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ==============================================================================
# DELETE /activities/{activity_name}/signup - Unregister Tests
# ==============================================================================

def test_unregister_success(client):
    """
    Test successful unregistration from an activity
    
    AAA:
    - Arrange: "michael@mergington.edu" is in Chess Club
    - Act: Send DELETE request to unregister
    - Assert: Participant is removed and success message returned
    """
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup?email={email}",
        headers={"Content-Type": "application/json"}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    assert email not in activities_response.json()[activity_name]["participants"]


def test_unregister_not_signed_up_returns_error(client):
    """
    Test that unregister fails when student is not signed up
    
    AAA:
    - Arrange: "notregistered@mergington.edu" is not in Chess Club
    - Act: Send DELETE request for non-participant
    - Assert: Returns 400 error with appropriate message
    """
    # Arrange
    activity_name = "Chess Club"
    email = "notregistered@mergington.edu"
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup?email={email}",
        headers={"Content-Type": "application/json"}
    )
    
    # Assert
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"]


def test_unregister_invalid_activity_returns_404(client):
    """
    Test that unregister fails with non-existent activity
    
    AAA:
    - Arrange: "Fake Activity" does not exist
    - Act: Send DELETE request for non-existent activity
    - Assert: Returns 404 error
    """
    # Arrange
    activity_name = "Fake Activity"
    email = "student@mergington.edu"
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup?email={email}",
        headers={"Content-Type": "application/json"}
    )
    
    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ==============================================================================
# Integration Tests
# ==============================================================================

def test_signup_and_unregister_flow(client):
    """
    Test complete signup and unregister flow
    
    AAA:
    - Arrange: "Programming Class" exists
    - Act: Sign up new student, then unregister them
    - Assert: Both operations succeed and state is correct
    """
    # Arrange
    activity_name = "Programming Class"
    email = "alice@mergington.edu"
    initial_count = len(client.get("/activities").json()[activity_name]["participants"])
    
    # Act & Assert - Signup
    signup_response = client.post(
        f"/activities/{activity_name}/signup?email={email}",
        headers={"Content-Type": "application/json"}
    )
    assert signup_response.status_code == 200
    assert email in client.get("/activities").json()[activity_name]["participants"]
    assert len(client.get("/activities").json()[activity_name]["participants"]) == initial_count + 1
    
    # Act & Assert - Unregister
    unregister_response = client.delete(
        f"/activities/{activity_name}/signup?email={email}",
        headers={"Content-Type": "application/json"}
    )
    assert unregister_response.status_code == 200
    assert email not in client.get("/activities").json()[activity_name]["participants"]
    assert len(client.get("/activities").json()[activity_name]["participants"]) == initial_count
