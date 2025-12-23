"""
Karmic Analytics Module

Generates interpretable karmic analytics for InsightFlow dashboards.
Provides trend analysis, visualization, and export capabilities.
"""
import os
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Conditional import for matplotlib
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    mdates = None

from database import karma_events_col, users_col
from utils.karma_engine import calculate_net_karma
import logging

# Setup logging
logger = logging.getLogger(__name__)

class KarmicAnalytics:
    """Generates karmic analytics for InsightFlow dashboards"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the karmic analytics engine"""
        self.config = config or {}
        self.export_directory = self.config.get("export_directory", "./analytics_exports")
        
        # Create export directory if it doesn't exist
        os.makedirs(self.export_directory, exist_ok=True)
        
        # Set matplotlib style if available
        if MATPLOTLIB_AVAILABLE and plt is not None:
            plt.style.use('seaborn-v0_8')
        
    def get_weekly_karma_trends(self, weeks: int = 4) -> Dict[str, Any]:
        """
        Get weekly karma trends for DharmaPoints and SevaPoints
        
        Args:
            weeks: Number of weeks to analyze
            
        Returns:
            Dictionary with weekly trends data
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(weeks=weeks)
        
        # Query karma events for the date range
        events = list(karma_events_col.find({
            "timestamp": {
                "$gte": start_date,
                "$lte": end_date
            }
        }).sort("timestamp", 1))
        
        # Group events by week
        weekly_data = {}
        for event in events:
            # Get week start (Monday)
            event_date = event["timestamp"]
            week_start = event_date - timedelta(days=event_date.weekday())
            week_key = week_start.strftime("%Y-%W")
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    "week_start": week_start,
                    "dharma_points": 0,
                    "seva_points": 0,
                    "paap_tokens": 0,
                    "punya_tokens": 0,
                    "event_count": 0
                }
            
            # Extract token data
            balances = event.get("balances", {})
            weekly_data[week_key]["dharma_points"] += balances.get("DharmaPoints", 0)
            weekly_data[week_key]["seva_points"] += balances.get("SevaPoints", 0)
            weekly_data[week_key]["paap_tokens"] += sum(balances.get("PaapTokens", {}).values())
            weekly_data[week_key]["punya_tokens"] += balances.get("PunyaTokens", 0)
            weekly_data[week_key]["event_count"] += 1
        
        # Convert to sorted list
        trends = sorted(weekly_data.values(), key=lambda x: x["week_start"])
        
        return {
            "period": f"{weeks} weeks",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "trends": trends
        }
    
    def get_paap_punya_ratio_trends(self, weeks: int = 4) -> Dict[str, Any]:
        """
        Get Paap/Punya ratio trends over time
        
        Args:
            weeks: Number of weeks to analyze
            
        Returns:
            Dictionary with ratio trends data
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(weeks=weeks)
        
        # Query karma events for the date range
        events = list(karma_events_col.find({
            "timestamp": {
                "$gte": start_date,
                "$lte": end_date
            }
        }).sort("timestamp", 1))
        
        # Group events by week
        weekly_data = {}
        for event in events:
            # Get week start (Monday)
            event_date = event["timestamp"]
            week_start = event_date - timedelta(days=event_date.weekday())
            week_key = week_start.strftime("%Y-%W")
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    "week_start": week_start,
                    "paap_total": 0,
                    "punya_total": 0,
                    "event_count": 0
                }
            
            # Extract token data
            balances = event.get("balances", {})
            paap_total = sum(balances.get("PaapTokens", {}).values())
            punya_total = balances.get("PunyaTokens", 0)
            
            weekly_data[week_key]["paap_total"] += paap_total
            weekly_data[week_key]["punya_total"] += punya_total
            weekly_data[week_key]["event_count"] += 1
        
        # Calculate ratios
        for week_data in weekly_data.values():
            total = week_data["paap_total"] + week_data["punya_total"]
            week_data["paap_ratio"] = week_data["paap_total"] / total if total > 0 else 0
            week_data["punya_ratio"] = week_data["punya_total"] / total if total > 0 else 0
            week_data["paap_punya_ratio"] = week_data["paap_total"] / week_data["punya_total"] if week_data["punya_total"] > 0 else 0
        
        # Convert to sorted list
        trends = sorted(weekly_data.values(), key=lambda x: x["week_start"])
        
        return {
            "period": f"{weeks} weeks",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "trends": trends
        }
    
    def generate_dharma_seva_flow_chart(self, weeks: int = 4, 
                                      filename: Optional[str] = None) -> str:
        """
        Generate a chart showing DharmaPoints/SevaPoints weekly flow
        
        Args:
            weeks: Number of weeks to analyze
            filename: Override export filename
            
        Returns:
            Path to the generated chart
        """
        if not MATPLOTLIB_AVAILABLE or plt is None:
            raise ImportError("Matplotlib is required for chart generation")
        
        # Get trends data
        trends_data = self.get_weekly_karma_trends(weeks)
        trends = trends_data["trends"]
        
        if not trends:
            # Create empty chart
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, "No data available", ha='center', va='center')
            ax.set_title("DharmaPoints/SevaPoints Weekly Flow")
        else:
            # Extract data for plotting
            weeks_labels = [t["week_start"].strftime("%Y-%W") for t in trends]
            dharma_points = [t["dharma_points"] for t in trends]
            seva_points = [t["seva_points"] for t in trends]
            
            # Create chart
            fig, ax = plt.subplots(figsize=(12, 6))
            x_pos = range(len(weeks_labels))
            
            ax.plot(x_pos, dharma_points, marker='o', linewidth=2, label='DharmaPoints')
            ax.plot(x_pos, seva_points, marker='s', linewidth=2, label='SevaPoints')
            
            ax.set_xlabel("Week")
            ax.set_ylabel("Points")
            ax.set_title("DharmaPoints/SevaPoints Weekly Flow")
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Set x-axis labels
            ax.set_xticks(x_pos)
            ax.set_xticklabels(weeks_labels, rotation=45)
            
            plt.tight_layout()
        
        # Determine filename
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"dharma_seva_flow_{timestamp}.png"
            
        # Full path
        filepath = os.path.join(self.export_directory, filename)
        
        # Save chart
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Dharma/Seva flow chart exported to {filepath}")
        return filepath
    
    def generate_paap_punya_ratio_chart(self, weeks: int = 4, 
                                      filename: Optional[str] = None) -> str:
        """
        Generate a chart showing Paap/Punya ratio over time
        
        Args:
            weeks: Number of weeks to analyze
            filename: Override export filename
            
        Returns:
            Path to the generated chart
        """
        if not MATPLOTLIB_AVAILABLE or plt is None:
            raise ImportError("Matplotlib is required for chart generation")
        
        # Get trends data
        trends_data = self.get_paap_punya_ratio_trends(weeks)
        trends = trends_data["trends"]
        
        if not trends:
            # Create empty chart
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, "No data available", ha='center', va='center')
            ax.set_title("Paap/Punya Ratio Over Time")
        else:
            # Extract data for plotting
            weeks_labels = [t["week_start"].strftime("%Y-%W") for t in trends]
            paap_punya_ratios = [t.get("paap_punya_ratio", 0) for t in trends]
            
            # Create chart
            fig, ax = plt.subplots(figsize=(12, 6))
            x_pos = range(len(weeks_labels))
            
            ax.plot(x_pos, paap_punya_ratios, marker='o', linewidth=2, color='purple')
            ax.set_xlabel("Week")
            ax.set_ylabel("Paap/Punya Ratio")
            ax.set_title("Paap/Punya Ratio Over Time")
            ax.grid(True, alpha=0.3)
            
            # Set x-axis labels
            ax.set_xticks(x_pos)
            ax.set_xticklabels(weeks_labels, rotation=45)
            
            plt.tight_layout()
        
        # Determine filename
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"paap_punya_ratio_{timestamp}.png"
            
        # Full path
        filepath = os.path.join(self.export_directory, filename)
        
        # Save chart
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Paap/Punya ratio chart exported to {filepath}")
        return filepath
    
    def export_weekly_summary_csv(self, weeks: int = 4, 
                                filename: Optional[str] = None) -> str:
        """
        Export weekly summary data to CSV
        
        Args:
            weeks: Number of weeks to analyze
            filename: Override export filename
            
        Returns:
            Path to the exported CSV file
        """
        # Get trends data
        dharma_seva_data = self.get_weekly_karma_trends(weeks)
        paap_punya_data = self.get_paap_punya_ratio_trends(weeks)
        
        # Combine data
        combined_data = []
        dharma_seva_trends = {t["week_start"].strftime("%Y-%W"): t for t in dharma_seva_data["trends"]}
        paap_punya_trends = {t["week_start"].strftime("%Y-%W"): t for t in paap_punya_data["trends"]}
        
        all_weeks = set(dharma_seva_trends.keys()) | set(paap_punya_trends.keys())
        
        for week_key in sorted(all_weeks):
            row = {"week": week_key}
            
            # Add Dharma/Seva data
            if week_key in dharma_seva_trends:
                ds_data = dharma_seva_trends[week_key]
                row.update({
                    "dharma_points": ds_data["dharma_points"],
                    "seva_points": ds_data["seva_points"],
                    "event_count_ds": ds_data["event_count"]
                })
            else:
                row.update({
                    "dharma_points": 0,
                    "seva_points": 0,
                    "event_count_ds": 0
                })
            
            # Add Paap/Punya data
            if week_key in paap_punya_trends:
                pp_data = paap_punya_trends[week_key]
                row.update({
                    "paap_tokens": pp_data["paap_total"],
                    "punya_tokens": pp_data["punya_total"],
                    "paap_punya_ratio": pp_data.get("paap_punya_ratio", 0),
                    "event_count_pp": pp_data["event_count"]
                })
            else:
                row.update({
                    "paap_tokens": 0,
                    "punya_tokens": 0,
                    "paap_punya_ratio": 0,
                    "event_count_pp": 0
                })
            
            combined_data.append(row)
        
        # Determine filename
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"weekly_summary_{timestamp}.csv"
            
        # Full path
        filepath = os.path.join(self.export_directory, filename)
        
        # Export to CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            if combined_data:
                fieldnames = combined_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(combined_data)
            else:
                # Write empty file with headers
                writer = csv.writer(csvfile)
                writer.writerow(["week", "dharma_points", "seva_points", "paap_tokens", 
                               "punya_tokens", "paap_punya_ratio", "event_count_ds", "event_count_pp"])
        
        logger.info(f"Weekly summary exported to {filepath}")
        return filepath
    
    def get_live_karmic_metrics(self) -> Dict[str, Any]:
        """
        Get live karmic metrics for the system
        
        Returns:
            Dictionary with current karmic metrics
        """
        # Get total users
        total_users = users_col.count_documents({})
        
        # Get recent karma events (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_events = list(karma_events_col.find({
            "timestamp": {"$gte": yesterday}
        }))
        
        # Calculate metrics
        total_events = len(recent_events)
        total_dharma = sum(event.get("balances", {}).get("DharmaPoints", 0) for event in recent_events)
        total_seva = sum(event.get("balances", {}).get("SevaPoints", 0) for event in recent_events)
        total_paap = sum(sum(event.get("balances", {}).get("PaapTokens", {}).values()) for event in recent_events)
        total_punya = sum(event.get("balances", {}).get("PunyaTokens", 0) for event in recent_events)
        
        # Calculate net karma for sample users (up to 10)
        sample_users = list(users_col.find().limit(10))
        avg_net_karma = 0.0
        if sample_users:
            net_karmas = [calculate_net_karma(user) for user in sample_users]
            if net_karmas:
                avg_net_karma = sum(float(k) if isinstance(k, (int, float)) else 0.0 for k in net_karmas) / len(net_karmas)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_users": total_users,
            "events_last_24h": total_events,
            "dharma_points_last_24h": total_dharma,
            "seva_points_last_24h": total_seva,
            "paap_tokens_last_24h": total_paap,
            "punya_tokens_last_24h": total_punya,
            "average_net_karma_sample": round(avg_net_karma, 2),
            "health_status": "operational"
        }

# Global instance
karmic_analytics = KarmicAnalytics()

# Convenience functions
def get_weekly_karma_trends(weeks: int = 4) -> Dict[str, Any]:
    """Get weekly karma trends"""
    return karmic_analytics.get_weekly_karma_trends(weeks)

def get_paap_punya_ratio_trends(weeks: int = 4) -> Dict[str, Any]:
    """Get Paap/Punya ratio trends"""
    return karmic_analytics.get_paap_punya_ratio_trends(weeks)

def generate_dharma_seva_flow_chart(weeks: int = 4, filename: Optional[str] = None) -> str:
    """Generate DharmaPoints/SevaPoints flow chart"""
    return karmic_analytics.generate_dharma_seva_flow_chart(weeks, filename)

def generate_paap_punya_ratio_chart(weeks: int = 4, filename: Optional[str] = None) -> str:
    """Generate Paap/Punya ratio chart"""
    return karmic_analytics.generate_paap_punya_ratio_chart(weeks, filename)

def export_weekly_summary_csv(weeks: int = 4, filename: Optional[str] = None) -> str:
    """Export weekly summary to CSV"""
    return karmic_analytics.export_weekly_summary_csv(weeks, filename)

def get_live_karmic_metrics() -> Dict[str, Any]:
    """Get live karmic metrics"""
    return karmic_analytics.get_live_karmic_metrics()