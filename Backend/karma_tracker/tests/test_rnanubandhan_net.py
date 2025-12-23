"""
Test suite for Rnanubandhan Network Analyzer functionality
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.rnanubandhan_net import RnanubandhanNetworkAnalyzer
from utils.rnanubandhan import rnanubandhan_manager
from database import users_col, rnanubandhan_col

# Test users
test_users = [
    {
        "user_id": "test_user_001",
        "role": "learner",
        "balances": {
            "DharmaPoints": 100,
            "SevaPoints": 80,
            "PunyaTokens": 70
        }
    },
    {
        "user_id": "test_user_002",
        "role": "learner",
        "balances": {
            "DharmaPoints": 90,
            "SevaPoints": 70,
            "PunyaTokens": 60
        }
    },
    {
        "user_id": "test_user_003",
        "role": "learner",
        "balances": {
            "DharmaPoints": 80,
            "SevaPoints": 60,
            "PunyaTokens": 50
        }
    }
]

def setup_test_data():
    """Set up test users and relationships in the database"""
    # Clear existing test data
    user_ids = [user["user_id"] for user in test_users]
    users_col.delete_many({"user_id": {"$in": user_ids}})
    rnanubandhan_col.delete_many({
        "$or": [
            {"debtor_id": {"$in": user_ids}},
            {"receiver_id": {"$in": user_ids}}
        ]
    })
    
    # Insert test users
    users_col.insert_many(test_users)
    
    # Create test relationships
    relationships = [
        {
            "debtor_id": "test_user_001",
            "receiver_id": "test_user_002",
            "action_type": "harm_action",
            "severity": "medium",
            "amount": 25.0,
            "description": "Caused emotional harm",
            "status": "active"
        },
        {
            "debtor_id": "test_user_002",
            "receiver_id": "test_user_001",
            "action_type": "help_action",
            "severity": "minor",
            "amount": 15.0,
            "description": "Provided assistance",
            "status": "active"
        },
        {
            "debtor_id": "test_user_001",
            "receiver_id": "test_user_003",
            "action_type": "harm_action",
            "severity": "minor",
            "amount": 10.0,
            "description": "Minor inconvenience",
            "status": "active"
        },
        {
            "debtor_id": "test_user_003",
            "receiver_id": "test_user_002",
            "action_type": "help_action",
            "severity": "medium",
            "amount": 20.0,
            "description": "Significant help",
            "status": "active"
        }
    ]
    
    # Insert relationships
    for rel in relationships:
        rel["created_at"] = rel["updated_at"] = "2024-01-01T00:00:00Z"
        rnanubandhan_col.insert_one(rel)

def teardown_test_data():
    """Clean up test data"""
    # Remove test users
    user_ids = [user["user_id"] for user in test_users]
    users_col.delete_many({"user_id": {"$in": user_ids}})
    
    # Remove test relationships
    rnanubandhan_col.delete_many({
        "$or": [
            {"debtor_id": {"$in": user_ids}},
            {"receiver_id": {"$in": user_ids}}
        ]
    })

def test_network_analyzer_initialization():
    """Test RnanubandhanNetworkAnalyzer initialization"""
    try:
        analyzer = RnanubandhanNetworkAnalyzer()
        assert analyzer is not None
        print("✓ RnanubandhanNetworkAnalyzer initialization test passed")
        return True
    except Exception as e:
        print(f"✗ RnanubandhanNetworkAnalyzer initialization test failed: {e}")
        return False

def test_build_network_graph():
    """Test building network graph"""
    # Setup
    setup_test_data()
    
    try:
        # Create analyzer
        analyzer = RnanubandhanNetworkAnalyzer()
        
        # Test building full network graph
        G = analyzer.build_network_graph()
        
        # Assertions
        assert G is not None
        assert G.number_of_nodes() >= 3
        assert G.number_of_edges() >= 4
        
        # Test building filtered network graph
        G_filtered = analyzer.build_network_graph(["test_user_001"])
        assert G_filtered is not None
        
        print("✓ Build Network Graph test passed")
        return True
        
    except Exception as e:
        print(f"✗ Build Network Graph test failed: {e}")
        return False
    finally:
        # Teardown
        teardown_test_data()

def test_get_network_metrics():
    """Test getting network metrics"""
    # Setup
    setup_test_data()
    
    try:
        # Create analyzer
        analyzer = RnanubandhanNetworkAnalyzer()
        
        # Test getting metrics for test_user_001
        metrics = analyzer.get_network_metrics("test_user_001")
        
        # Assertions
        assert "user_id" in metrics
        assert "in_degree" in metrics
        assert "out_degree" in metrics
        assert "total_credit" in metrics
        assert "total_debt" in metrics
        assert "net_position" in metrics
        assert "creditors_count" in metrics
        assert "debtors_count" in metrics
        assert "creditors" in metrics
        assert "debtors" in metrics
        
        # Check specific values
        assert metrics["user_id"] == "test_user_001"
        assert metrics["total_debt"] == 35.0  # 25 + 10
        assert metrics["total_credit"] == 15.0
        
        print("✓ Get Network Metrics test passed")
        return True
        
    except Exception as e:
        print(f"✗ Get Network Metrics test failed: {e}")
        return False
    finally:
        # Teardown
        teardown_test_data()

def test_get_relationship_patterns():
    """Test getting relationship patterns"""
    # Setup
    setup_test_data()
    
    try:
        # Create analyzer
        analyzer = RnanubandhanNetworkAnalyzer()
        
        # Test getting patterns for test_user_001
        patterns = analyzer.get_relationship_patterns("test_user_001")
        
        # Assertions
        assert "user_id" in patterns
        assert "severity_distribution" in patterns
        assert "action_type_distribution" in patterns
        assert "status_distribution" in patterns
        assert "total_debt" in patterns
        assert "total_credit" in patterns
        assert "net_position" in patterns
        assert "debt_to_credit_ratio" in patterns
        assert "relationship_count" in patterns
        
        # Check specific values
        assert patterns["user_id"] == "test_user_001"
        assert patterns["total_debt"] == 35.0  # 25 + 10
        assert patterns["total_credit"] == 15.0
        # test_user_001 has 2 debts (to user_002: 25, to user_003: 10) 
        # and 1 credit (from user_002: 15)
        # Total relationships = 2 debts + 1 credit = 3
        assert patterns["relationship_count"] == 3
        
        print("✓ Get Relationship Patterns test passed")
        return True
        
    except Exception as e:
        print(f"✗ Get Relationship Patterns test failed: {e}")
        return False
    finally:
        # Teardown
        teardown_test_data()

def test_get_network_summary():
    """Test getting network summary"""
    # Setup
    setup_test_data()
    
    try:
        # Create analyzer
        analyzer = RnanubandhanNetworkAnalyzer()
        
        # Test getting summary for test_user_001
        summary = analyzer.get_network_summary("test_user_001")
        
        # Assertions
        assert "user_id" in summary
        assert "timestamp" in summary
        assert "metrics" in summary
        assert "patterns" in summary
        assert "visualization" in summary
        assert "recommendations" in summary
        
        # Check metrics structure
        metrics = summary["metrics"]
        assert "in_degree" in metrics
        assert "out_degree" in metrics
        assert "total_credit" in metrics
        assert "total_debt" in metrics
        
        # Check patterns structure
        patterns = summary["patterns"]
        assert "severity_distribution" in patterns
        assert "action_type_distribution" in patterns
        
        # Check visualization structure
        visualization = summary["visualization"]
        assert "nodes" in visualization
        assert "edges" in visualization
        
        print("✓ Get Network Summary test passed")
        return True
        
    except Exception as e:
        print(f"✗ Get Network Summary test failed: {e}")
        return False
    finally:
        # Teardown
        teardown_test_data()

def test_find_karmic_communities():
    """Test finding karmic communities"""
    # Setup
    setup_test_data()
    
    try:
        # Create analyzer
        analyzer = RnanubandhanNetworkAnalyzer()
        
        # Test finding communities
        communities = analyzer.find_karmic_communities(min_size=2)
        
        # Assertions
        assert isinstance(communities, list)
        
        # Check community structure
        if len(communities) > 0:
            community = communities[0]
            assert "community_id" in community
            assert "members" in community
            assert "size" in community
            assert "total_relationships" in community
            assert "total_karmic_debt" in community
        
        print("✓ Find Karmic Communities test passed")
        return True
        
    except Exception as e:
        print(f"✗ Find Karmic Communities test failed: {e}")
        return False
    finally:
        # Teardown
        teardown_test_data()

def test_error_handling():
    """Test error handling"""
    try:
        # Create analyzer
        analyzer = RnanubandhanNetworkAnalyzer()
        
        # Test getting metrics for non-existent user
        metrics = analyzer.get_network_metrics("non_existent_user")
        # Should return error message
        assert "error" in metrics
        
        print("✓ Error Handling test passed")
        return True
        
    except Exception as e:
        print(f"✗ Error Handling test failed: {e}")
        return False

if __name__ == "__main__":
    print("Running Rnanubandhan Network Analyzer tests...")
    print("=" * 50)
    
    tests = [
        test_network_analyzer_initialization,
        test_build_network_graph,
        test_get_network_metrics,
        test_get_relationship_patterns,
        test_get_network_summary,
        test_find_karmic_communities,
        test_error_handling
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All Rnanubandhan Network Analyzer tests passed!")
    else:
        print("⚠️  Some tests failed.")