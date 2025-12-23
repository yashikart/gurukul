"""
Test suite for Karmic Analytics
"""
import sys
import os
import tempfile
import json
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.karmic_analytics import (
    KarmicAnalytics,
    get_weekly_karma_trends,
    get_paap_punya_ratio_trends,
    export_weekly_summary_csv,
    get_live_karmic_metrics
)

def test_karmic_analytics_initialization():
    """Test initialization of KarmicAnalytics"""
    # Test with default config
    analytics = KarmicAnalytics()
    assert analytics.export_directory == "./analytics_exports"
    
    # Test with custom config
    with tempfile.TemporaryDirectory() as temp_dir:
        config = {"export_directory": temp_dir}
        analytics = KarmicAnalytics(config)
        assert analytics.export_directory == temp_dir
    
    print("✓ KarmicAnalytics initialization test passed")

def test_weekly_karma_trends():
    """Test getting weekly karma trends"""
    trends = get_weekly_karma_trends(weeks=2)
    
    # Check structure
    assert "period" in trends
    assert "start_date" in trends
    assert "end_date" in trends
    assert "trends" in trends
    
    # Check types
    assert isinstance(trends["period"], str)
    assert isinstance(trends["trends"], list)
    
    print("✓ Weekly karma trends test passed")

def test_paap_punya_ratio_trends():
    """Test getting Paap/Punya ratio trends"""
    trends = get_paap_punya_ratio_trends(weeks=2)
    
    # Check structure
    assert "period" in trends
    assert "start_date" in trends
    assert "end_date" in trends
    assert "trends" in trends
    
    # Check types
    assert isinstance(trends["period"], str)
    assert isinstance(trends["trends"], list)
    
    print("✓ Paap/Punya ratio trends test passed")

def test_weekly_summary_export():
    """Test exporting weekly summary to CSV"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create analytics with temporary directory
        analytics = KarmicAnalytics({"export_directory": temp_dir})
        
        # Patch the global instance
        import utils.karmic_analytics
        utils.karmic_analytics.karmic_analytics = analytics
        
        # Export summary
        filepath = export_weekly_summary_csv(weeks=2, filename="test_summary.csv")
        
        # Check that file was created
        assert os.path.exists(filepath)
        
        # Check file content
        with open(filepath, 'r') as f:
            content = f.read()
            
        assert "week" in content
        assert "dharma_points" in content
        
        print("✓ Weekly summary export test passed")

def test_live_karmic_metrics():
    """Test getting live karmic metrics"""
    metrics = get_live_karmic_metrics()
    
    # Check structure
    assert "timestamp" in metrics
    assert "total_users" in metrics
    assert "events_last_24h" in metrics
    assert "dharma_points_last_24h" in metrics
    assert "seva_points_last_24h" in metrics
    assert "paap_tokens_last_24h" in metrics
    assert "punya_tokens_last_24h" in metrics
    assert "average_net_karma_sample" in metrics
    assert "health_status" in metrics
    
    # Check types
    assert isinstance(metrics["total_users"], int)
    assert isinstance(metrics["events_last_24h"], int)
    assert isinstance(metrics["average_net_karma_sample"], float)
    assert isinstance(metrics["health_status"], str)
    
    print("✓ Live karmic metrics test passed")

def test_analytics_with_sample_data():
    """Test analytics with sample data"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create analytics with temporary directory
        analytics = KarmicAnalytics({"export_directory": temp_dir})
        
        # Test data methods directly
        trends_data = analytics.get_weekly_karma_trends(weeks=1)
        assert "period" in trends_data
        assert "trends" in trends_data
        
        ratio_data = analytics.get_paap_punya_ratio_trends(weeks=1)
        assert "period" in ratio_data
        assert "trends" in ratio_data
        
        print("✓ Analytics with sample data test passed")

if __name__ == "__main__":
    print("Running Karmic Analytics Tests...")
    
    test_karmic_analytics_initialization()
    test_weekly_karma_trends()
    test_paap_punya_ratio_trends()
    test_weekly_summary_export()
    test_live_karmic_metrics()
    test_analytics_with_sample_data()
    
    print("\n🎉 All karmic analytics tests passed!")