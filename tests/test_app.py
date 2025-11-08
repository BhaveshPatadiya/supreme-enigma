import pytest
from fastapi.testclient import TestClient
from src.app import app

@pytest.fixture
def client():
    return TestClient(app)

def test_root_redirect(client):
    """Test that root endpoint redirects to static/index.html"""
    response = client.get("/")
    assert response.status_code == 200 or response.status_code == 307
    
def test_get_activities(client):
    """Test getting the list of activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0
    
    # Verify activity structure
    for activity_name, details in data.items():
        assert isinstance(activity_name, str)
        assert isinstance(details, dict)
        assert "description" in details
        assert "schedule" in details
        assert "max_participants" in details
        assert "participants" in details
        assert isinstance(details["participants"], list)

def test_signup_flow(client):
    """Test the complete signup flow for an activity"""
    # Get available activities
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    
    # Pick first activity for testing
    activity_name = next(iter(activities.keys()))
    test_email = "test_student@mergington.edu"
    
    # Try signing up
    response = client.post(f"/activities/{activity_name}/signup", params={"email": test_email})
    assert response.status_code == 200
    assert "message" in response.json()
    
    # Verify student appears in participants
    response = client.get("/activities")
    assert response.status_code == 200
    updated_activities = response.json()
    assert test_email in updated_activities[activity_name]["participants"]
    
    # Test duplicate signup prevention
    response = client.post(f"/activities/{activity_name}/signup", params={"email": test_email})
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()

def test_unregister_flow(client):
    """Test the complete unregister flow for an activity"""
    # First sign up a test user
    activity_name = "Chess Club"
    test_email = "test_unregister@mergington.edu"
    
    # Sign up the test user
    response = client.post(f"/activities/{activity_name}/signup", params={"email": test_email})
    assert response.status_code == 200
    
    # Verify registration
    response = client.get("/activities")
    activities = response.json()
    assert test_email in activities[activity_name]["participants"]
    
    # Test unregistration
    response = client.delete(f"/activities/{activity_name}/unregister", params={"email": test_email})
    assert response.status_code == 200
    assert "message" in response.json()
    
    # Verify student is removed
    response = client.get("/activities")
    updated_activities = response.json()
    assert test_email not in updated_activities[activity_name]["participants"]
    
    # Test unregistering non-registered student
    response = client.delete(f"/activities/{activity_name}/unregister", params={"email": test_email})
    assert response.status_code == 400
    assert "not registered" in response.json()["detail"].lower()

def test_invalid_activity(client):
    """Test handling of invalid activity names"""
    invalid_activity = "NonexistentActivity"
    test_email = "test@mergington.edu"
    
    # Test signup for invalid activity
    response = client.post(f"/activities/{invalid_activity}/signup", params={"email": test_email})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    
    # Test unregister from invalid activity
    response = client.delete(f"/activities/{invalid_activity}/unregister", params={"email": test_email})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()