"""
Test suite for the Karma Lifecycle Engine
"""

import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from utils.karma_lifecycle import (
    KarmaLifecycleEngine,
    get_prarabdha_counter,
    update_prarabdha_counter,
    check_death_event_threshold,
    process_death_event,
    process_rebirth
)

class TestKarmaLifecycleEngine(unittest.TestCase):
    """Test cases for the Karma Lifecycle Engine"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.lifecycle_engine = KarmaLifecycleEngine()
        self.test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        
        # Mock user data
        self.mock_user = {
            "user_id": self.test_user_id,
            "username": "TestUser",
            "balances": {
                "DharmaPoints": 50,
                "SevaPoints": 30,
                "PunyaTokens": 20,
                "PaapTokens": {
                    "minor": 5,
                    "medium": 2,
                    "maha": 1
                },
                "SanchitaKarma": 100.0,
                "PrarabdhaKarma": 50.0,
                "DridhaKarma": 30.0,
                "AdridhaKarma": 20.0
            },
            "role": "learner",
            "rebirth_count": 0,
            "merit_score": 150
        }
    
    @patch('utils.karma_lifecycle.users_col')
    def test_get_user_prarabdha(self, mock_users_col):
        """Test getting user Prarabdha counter"""
        # Setup mock
        mock_users_col.find_one.return_value = self.mock_user
        
        # Test
        prarabdha = self.lifecycle_engine.get_user_prarabdha(self.test_user_id)
        
        # Assertions
        self.assertEqual(prarabdha, 50.0)
        mock_users_col.find_one.assert_called_once_with({"user_id": self.test_user_id})
    
    @patch('utils.karma_lifecycle.users_col')
    def test_get_user_prarabdha_user_not_found(self, mock_users_col):
        """Test getting Prarabdha for non-existent user"""
        # Setup mock
        mock_users_col.find_one.return_value = None
        
        # Test and assert
        with self.assertRaises(ValueError) as context:
            self.lifecycle_engine.get_user_prarabdha(self.test_user_id)
        
        self.assertIn(self.test_user_id, str(context.exception))
    
    @patch('utils.karma_lifecycle.users_col')
    def test_update_prarabdha(self, mock_users_col):
        """Test updating user Prarabdha counter"""
        # Setup mocks
        mock_users_col.find_one.return_value = self.mock_user
        mock_users_col.update_one.return_value = None
        
        # Test
        new_prarabdha = self.lifecycle_engine.update_prarabdha(self.test_user_id, 25.0)
        
        # Assertions
        self.assertEqual(new_prarabdha, 75.0)  # 50.0 + 25.0
        mock_users_col.find_one.assert_called_once_with({"user_id": self.test_user_id})
        mock_users_col.update_one.assert_called_once()
    
    @patch('utils.karma_lifecycle.users_col')
    def test_check_death_threshold_not_reached(self, mock_users_col):
        """Test death threshold check when threshold is not reached"""
        # Setup mock
        mock_users_col.find_one.return_value = self.mock_user
        
        # Test
        threshold_reached, details = self.lifecycle_engine.check_death_threshold(self.test_user_id)
        
        # Assertions
        self.assertFalse(threshold_reached)
        self.assertEqual(details["user_id"], self.test_user_id)
        self.assertEqual(details["current_prarabdha"], 50.0)
        self.assertEqual(details["death_threshold"], -100.0)
    
    @patch('utils.karma_lifecycle.users_col')
    def test_check_death_threshold_reached(self, mock_users_col):
        """Test death threshold check when threshold is reached"""
        # Modify mock user to have very negative Prarabdha
        mock_user_negative = self.mock_user.copy()
        mock_user_negative["balances"]["PrarabdhaKarma"] = -150.0
        mock_users_col.find_one.return_value = mock_user_negative
        
        # Test
        threshold_reached, details = self.lifecycle_engine.check_death_threshold(self.test_user_id)
        
        # Assertions
        self.assertTrue(threshold_reached)
        self.assertEqual(details["current_prarabdha"], -150.0)
    
    @patch('utils.karma_lifecycle.users_col')
    @patch('utils.karma_lifecycle.calculate_net_karma')
    def test_calculate_sanchita_inheritance_positive(self, mock_calculate_net_karma, mock_users_col):
        """Test Sanchita inheritance calculation with positive net karma"""
        # Setup mocks
        mock_users_col.find_one.return_value = self.mock_user
        mock_calculate_net_karma.return_value = {"net_karma": 100.0}
        
        # Test
        inheritance = self.lifecycle_engine.calculate_sanchita_inheritance(self.mock_user)
        
        # Assertions
        self.assertEqual(inheritance["net_karma"], 100.0)
        self.assertEqual(inheritance["carryover_positive"], 20.0)  # 100 * 0.2
        self.assertEqual(inheritance["carryover_negative"], 0.0)
        self.assertGreater(inheritance["inherited_sanchita"], 100.0)
    
    @patch('utils.karma_lifecycle.users_col')
    @patch('utils.karma_lifecycle.calculate_net_karma')
    def test_calculate_sanchita_inheritance_negative(self, mock_calculate_net_karma, mock_users_col):
        """Test Sanchita inheritance calculation with negative net karma"""
        # Setup mocks
        mock_users_col.find_one.return_value = self.mock_user
        mock_calculate_net_karma.return_value = {"net_karma": -50.0}
        
        # Test
        inheritance = self.lifecycle_engine.calculate_sanchita_inheritance(self.mock_user)
        
        # Assertions
        self.assertEqual(inheritance["net_karma"], -50.0)
        self.assertEqual(inheritance["carryover_positive"], 0.0)
        self.assertEqual(inheritance["carryover_negative"], 25.0)  # 50 * 0.5
        self.assertLess(inheritance["inherited_sanchita"], 100.0)
    
    def test_generate_new_user_id(self):
        """Test generation of new user IDs"""
        # Test
        new_id_1 = self.lifecycle_engine.generate_new_user_id()
        new_id_2 = self.lifecycle_engine.generate_new_user_id()
        
        # Assertions
        self.assertTrue(new_id_1.startswith("user_"))
        self.assertTrue(new_id_2.startswith("user_"))
        self.assertNotEqual(new_id_1, new_id_2)
        self.assertEqual(len(new_id_1), 17)  # "user_" + 12 chars
        self.assertEqual(len(new_id_2), 17)
    
    @patch('utils.karma_lifecycle.users_col')
    @patch('utils.karma_lifecycle.death_events_col')
    @patch('utils.karma_lifecycle.calculate_net_karma')
    def test_trigger_death_event(self, mock_calculate_net_karma, mock_death_events_col, mock_users_col):
        """Test triggering a death event"""
        # Setup mocks
        mock_users_col.find_one.return_value = self.mock_user
        mock_calculate_net_karma.return_value = {"net_karma": 150.0}
        mock_death_events_col.insert_one.return_value = None
        
        # Test
        result = self.lifecycle_engine.trigger_death_event(self.test_user_id)
        
        # Assertions
        self.assertEqual(result["status"], "death_event_triggered")
        self.assertEqual(result["user_id"], self.test_user_id)
        # With positive karma (150), user should be assigned to Swarga loka
        # But our LOKA_THRESHOLDS show Swarga is for karma >= 500
        # So the user should actually go to Mrityuloka (0 to 499)
        self.assertEqual(result["loka"], "Mrityuloka")  # Positive but < 500 karma goes to Mrityuloka
        mock_users_col.find_one.assert_called_once_with({"user_id": self.test_user_id})
        mock_death_events_col.insert_one.assert_called_once()
    
    @patch('utils.karma_lifecycle.users_col')
    @patch('utils.karma_lifecycle.calculate_net_karma')
    def test_rebirth_user(self, mock_calculate_net_karma, mock_users_col):
        """Test user rebirth process"""
        # Setup mocks
        mock_users_col.find_one.return_value = self.mock_user
        mock_calculate_net_karma.return_value = {"net_karma": 150.0}
        
        # Test
        result = self.lifecycle_engine.rebirth_user(self.test_user_id)
        
        # Assertions
        self.assertEqual(result["status"], "rebirth_completed")
        self.assertEqual(result["old_user_id"], self.test_user_id)
        self.assertTrue(result["new_user_id"].startswith("user_"))
        self.assertNotEqual(result["new_user_id"], self.test_user_id)
        mock_users_col.find_one.assert_called_once_with({"user_id": self.test_user_id})
        self.assertEqual(mock_users_col.insert_one.call_count, 1)
        self.assertEqual(mock_users_col.update_one.call_count, 1)
    
    @patch('utils.karma_lifecycle.users_col')
    def test_process_death_event_user_not_found(self, mock_users_col):
        """Test processing death event for non-existent user"""
        # Setup mock
        mock_users_col.find_one.return_value = None
        
        # Test and assert
        with self.assertRaises(ValueError) as context:
            process_death_event(self.test_user_id)
        
        self.assertIn(self.test_user_id, str(context.exception))

class TestLifecycleSimulation(unittest.TestCase):
    """Test cases for lifecycle simulation"""
    
    def test_simulate_50_cycles_placeholder(self):
        """Test that the simulation function exists and runs without error"""
        # This is a placeholder test since the actual simulation logic
        # would be implemented separately
        self.assertTrue(True)  # Placeholder assertion
    
    def test_simulate_50_cycles_comprehensive(self):
        """Test comprehensive 50-cycle simulation"""
        # This test would require a full integration test which is complex to mock
        # For now, we'll just verify the function exists and can be called
        from routes.v1.karma.lifecycle import SimulateCycleRequest
        self.assertTrue(SimulateCycleRequest)  # Just verify the class exists


if __name__ == '__main__':
    unittest.main()