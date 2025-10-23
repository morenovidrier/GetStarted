from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_root_redirect():
    response = client.get("/")
    assert response.status_code == 200 or response.status_code == 307
    
def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    assert isinstance(activities, dict)
    assert len(activities) > 0
    
    # Verify activity structure
    for activity_name, details in activities.items():
        assert isinstance(activity_name, str)
        assert isinstance(details, dict)
        assert "description" in details
        assert "schedule" in details
        assert "max_participants" in details
        assert "participants" in details
        assert isinstance(details["participants"], list)

def test_signup_for_activity():
    # Test successful signup
    response = client.post("/activities/Chess Club/signup?email=test@mergington.edu")
    assert response.status_code == 200
    assert "message" in response.json()
    
    # Test duplicate signup
    response = client.post("/activities/Chess Club/signup?email=test@mergington.edu")
    assert response.status_code == 400
    assert "detail" in response.json()
    
    # Test signup for non-existent activity
    response = client.post("/activities/NonExistentClub/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert "detail" in response.json()

def test_unregister_from_activity():
    # First sign up a test user
    email = "testunregister@mergington.edu"
    activity = "Chess Club"
    
    # Sign up the user first
    client.post(f"/activities/{activity}/signup?email={email}")
    
    # Test successful unregistration
    response = client.post(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 200
    assert "message" in response.json()
    
    # Test unregister when not registered
    response = client.post(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 400
    assert "detail" in response.json()
    
    # Test unregister from non-existent activity
    response = client.post("/activities/NonExistentClub/unregister?email=test@mergington.edu")
    assert response.status_code == 404
    assert "detail" in response.json()

def test_activity_capacity():
    # Use Chess Club which has a max_participants of 12
    activity_name = "Chess Club"
    
    # Get current participants
    activities = client.get("/activities").json()
    current_participants = activities[activity_name]["participants"].copy()
    max_participants = activities[activity_name]["max_participants"]
    
    try:
        # Calculate how many more participants we can add
        slots_available = max_participants - len(current_participants)
        
        # Try to add one more than capacity
        emails = [f"capacity_test_{i}@mergington.edu" for i in range(slots_available + 1)]
        
        # These should succeed
        for i in range(slots_available):
            response = client.post(f"/activities/{activity_name}/signup?email={emails[i]}")
            assert response.status_code == 200
        
        # This one should fail (capacity reached)
        response = client.post(f"/activities/{activity_name}/signup?email={emails[-1]}")
        assert response.status_code == 400
        assert "capacity" in response.json()["detail"].lower()
    
    finally:
        # Cleanup: unregister all test participants
        for email in emails:
            client.post(f"/activities/{activity_name}/unregister?email={email}")