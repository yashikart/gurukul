"""
Analytics Scheduler Module

Handles automatic scheduling of weekly karmic analytics generation.
"""
import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Optional
from utils.karmic_analytics import export_weekly_summary_csv

# Setup logging
logger = logging.getLogger(__name__)

class AnalyticsScheduler:
    """Scheduler for automatic karmic analytics generation"""
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize the analytics scheduler"""
        self.config = config or {}
        # Default to Monday at 1 AM for weekly summaries
        self.export_time = self.config.get("export_time", time(1, 0))  
        self.export_day = self.config.get("export_day", 0)  # 0 = Monday
        self.enabled = self.config.get("enabled", True)
        self.running = False
        self.task = None
        
    async def start_scheduler(self):
        """Start the analytics export scheduler"""
        if not self.enabled:
            logger.info("Analytics scheduler is disabled")
            return
            
        self.running = True
        logger.info(f"Analytics scheduler started, weekly export scheduled for {self.export_day} at {self.export_time}")
        
        while self.running:
            # Calculate time until next export
            now = datetime.now()
            
            # Find next export date (next occurrence of export_day)
            days_ahead = self.export_day - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7  # Move to next week
            
            next_export_date = now.date() + timedelta(days=days_ahead)
            next_export = datetime.combine(next_export_date, self.export_time)
            
            # If it's already past the export time today and today is the export day, schedule for next week
            if now.weekday() == self.export_day and now.time() > self.export_time:
                next_export = next_export + timedelta(weeks=1)
            
            # Calculate sleep duration
            sleep_seconds = (next_export - now).total_seconds()
            
            logger.info(f"Next export scheduled for {next_export} ({sleep_seconds} seconds from now)")
            
            # Wait until next export time
            await asyncio.sleep(sleep_seconds)
            
            # Perform export
            if self.running:
                await self._perform_export()
    
    async def _perform_export(self):
        """Perform the weekly analytics export"""
        try:
            logger.info("Starting weekly analytics export...")
            filepath = export_weekly_summary_csv(weeks=4)
            logger.info(f"Weekly analytics export completed successfully: {filepath}")
        except Exception as e:
            logger.error(f"Error during weekly analytics export: {str(e)}")
    
    def stop_scheduler(self):
        """Stop the analytics export scheduler"""
        self.running = False
        if self.task:
            self.task.cancel()
        logger.info("Analytics scheduler stopped")
    
    def set_export_schedule(self, export_time: time, export_day: int):
        """Set the weekly export time and day"""
        self.export_time = export_time
        self.export_day = export_day
        logger.info(f"Export schedule updated to {export_day} at {export_time}")
    
    def enable_scheduler(self):
        """Enable the scheduler"""
        self.enabled = True
        logger.info("Analytics scheduler enabled")
    
    def disable_scheduler(self):
        """Disable the scheduler"""
        self.enabled = False
        logger.info("Analytics scheduler disabled")

# Global instance
analytics_scheduler = AnalyticsScheduler()

# Convenience functions
async def start_analytics_scheduler():
    """Start the analytics scheduler"""
    await analytics_scheduler.start_scheduler()

def stop_analytics_scheduler():
    """Stop the analytics scheduler"""
    analytics_scheduler.stop_scheduler()

def set_analytics_export_schedule(export_time: time, export_day: int):
    """Set the analytics export schedule"""
    analytics_scheduler.set_export_schedule(export_time, export_day)

def enable_analytics_scheduler():
    """Enable the analytics scheduler"""
    analytics_scheduler.enable_scheduler()

def disable_analytics_scheduler():
    """Disable the analytics scheduler"""
    analytics_scheduler.disable_scheduler()