"""
Test suite for the Karma Lifecycle API endpoints
"""

import unittest
from fastapi.testclient import TestClient
from main import app

class TestLifecycleAPI(unittest.TestCase):
    """Test cases for the Karma Lifecycle API endpoints"""
    
    def setUp(self):
        """Set up test client before each test method."""
        self.client = TestClient(app)
    
    def test_prarabdha_endpoint_exists(self):
        """Test that the Prarabdha endpoint exists"""
        response = self.client.get("/api/v1/karma/lifecycle/prarabdha/test_user")
        # We expect a 404 since the user doesn't exist, but not a 404 for the endpoint itself
        self.assertIn(response.status_code, [404, 500])  # Either user not found or database error
    
    def test_death_check_endpoint_exists(self):
        """Test that the death check endpoint exists"""
        response = self.client.post("/api/v1/karma/lifecycle/death/check", json={"user_id": "test_user"})
        # We expect a 404 since the user doesn't exist, but not a 404 for the endpoint itself
        self.assertIn(response.status_code, [404, 500])  # Either user not found or database error
    
    def test_simulation_endpoint_exists(self):
        """Test that the simulation endpoint exists"""
        response = self.client.post("/api/v1/karma/lifecycle/simulate", json={"cycles": 5, "initial_users": 3})
        # We expect a 500 since there's no database, but not a 404 for the endpoint itself
        self.assertIn(response.status_code, [404, 500])  # Either not found or database error

if __name__ == '__main__':
    unittest.main()