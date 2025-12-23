#!/usr/bin/env python3
"""
Demo script for Karmic Analytics
Shows how to use the karmic analytics features
"""
import sys
import os
import tempfile
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.karmic_analytics import (
    KarmicAnalytics,
    get_weekly_karma_trends,
    get_paap_punya_ratio_trends,
    export_weekly_summary_csv,
    get_live_karmic_metrics
)

def demo_karmic_analytics():
    """Demonstrate karmic analytics functionality"""
    print("Karmic Analytics Demo")
    print("=" * 30)
    
    # Create analytics with temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory for exports: {temp_dir}")
        
        analytics = KarmicAnalytics({"export_directory": temp_dir})
        
        # Get weekly karma trends
        print("\n1. Getting weekly karma trends...")
        trends = get_weekly_karma_trends(weeks=2)
        print(f"   Period: {trends['period']}")
        print(f"   Data points: {len(trends['trends'])}")
        
        # Get Paap/Punya ratio trends
        print("\n2. Getting Paap/Punya ratio trends...")
        ratio_trends = get_paap_punya_ratio_trends(weeks=2)
        print(f"   Period: {ratio_trends['period']}")
        print(f"   Data points: {len(ratio_trends['trends'])}")
        
        # Export weekly summary
        print("\n3. Exporting weekly summary to CSV...")
        try:
            csv_file = export_weekly_summary_csv(weeks=2, filename="demo_weekly_summary.csv")
            print(f"   CSV exported to: {csv_file}")
            
            # Show file size
            if os.path.exists(csv_file):
                size = os.path.getsize(csv_file)
                print(f"   File size: {size} bytes")
        except Exception as e:
            print(f"   Error exporting CSV: {e}")
        
        # Get live metrics
        print("\n4. Getting live karmic metrics...")
        metrics = get_live_karmic_metrics()
        print(f"   Total users: {metrics['total_users']}")
        print(f"   Events (last 24h): {metrics['events_last_24h']}")
        print(f"   Average net karma (sample): {metrics['average_net_karma_sample']}")
        print(f"   Health status: {metrics['health_status']}")
        
        print("\n5. Analytics functionality demo completed!")

def show_api_endpoints():
    """Show available API endpoints"""
    print("\nAvailable API Endpoints:")
    print("=" * 30)
    endpoints = [
        "GET /api/v1/analytics/karma_trends",
        "GET /api/v1/analytics/charts/dharma_seva_flow",
        "GET /api/v1/analytics/charts/paap_punya_ratio",
        "GET /api/v1/analytics/exports/weekly_summary",
        "GET /api/v1/analytics/metrics/live"
    ]
    
    for endpoint in endpoints:
        print(f"  {endpoint}")

if __name__ == "__main__":
    print("Karmic Analytics Demonstration")
    print("=" * 40)
    
    try:
        demo_karmic_analytics()
        show_api_endpoints()
        
        print("\n" + "=" * 40)
        print("🎉 Karmic analytics demo completed!")
        print("\nTo use the analytics API endpoints, start the server with:")
        print("  python main.py")
        print("\nThen access the endpoints via HTTP requests.")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()