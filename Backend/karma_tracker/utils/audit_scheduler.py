"""
Audit Scheduler Module

Handles automatic scheduling of daily audit snapshot exports.
"""
import asyncio
import logging
from datetime import datetime, time
from typing import Optional, Callable
from utils.audit_enhancer import auto_export_telemetry_feed

# Setup logging
logger = logging.getLogger(__name__)

class AuditScheduler:
    """Scheduler for automatic audit snapshot exports"""
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize the audit scheduler"""
        self.config = config or {}
        self.export_time = self.config.get("export_time", time(0, 0))  # Default to midnight
        self.enabled = self.config.get("enabled", True)
        self.running = False
        self.task = None
        
    async def start_scheduler(self):
        """Start the audit export scheduler"""
        if not self.enabled:
            logger.info("Audit scheduler is disabled")
            return
            
        self.running = True
        logger.info(f"Audit scheduler started, daily export scheduled for {self.export_time}")
        
        while self.running:
            # Calculate time until next export
            now = datetime.now()
            next_export = datetime.combine(now.date(), self.export_time)
            
            # If it's already past the export time today, schedule for tomorrow
            if now.time() > self.export_time:
                next_export = next_export.replace(day=next_export.day + 1)
            
            # Calculate sleep duration
            sleep_seconds = (next_export - now).total_seconds()
            
            logger.info(f"Next export scheduled for {next_export} ({sleep_seconds} seconds from now)")
            
            # Wait until next export time
            await asyncio.sleep(sleep_seconds)
            
            # Perform export
            if self.running:
                await self._perform_export()
    
    async def _perform_export(self):
        """Perform the daily audit export"""
        try:
            logger.info("Starting daily audit export...")
            filepath = auto_export_telemetry_feed()
            logger.info(f"Daily audit export completed successfully: {filepath}")
        except Exception as e:
            logger.error(f"Error during daily audit export: {str(e)}")
    
    def stop_scheduler(self):
        """Stop the audit export scheduler"""
        self.running = False
        if self.task:
            self.task.cancel()
        logger.info("Audit scheduler stopped")
    
    def set_export_time(self, export_time: time):
        """Set the daily export time"""
        self.export_time = export_time
        logger.info(f"Export time updated to {export_time}")
    
    def enable_scheduler(self):
        """Enable the scheduler"""
        self.enabled = True
        logger.info("Audit scheduler enabled")
    
    def disable_scheduler(self):
        """Disable the scheduler"""
        self.enabled = False
        logger.info("Audit scheduler disabled")

# Global instance
audit_scheduler = AuditScheduler()

# Convenience functions
async def start_audit_scheduler():
    """Start the audit scheduler"""
    await audit_scheduler.start_scheduler()

def stop_audit_scheduler():
    """Stop the audit scheduler"""
    audit_scheduler.stop_scheduler()

def set_audit_export_time(export_time: time):
    """Set the audit export time"""
    audit_scheduler.set_export_time(export_time)

def enable_audit_scheduler():
    """Enable the audit scheduler"""
    audit_scheduler.enable_scheduler()

def disable_audit_scheduler():
    """Disable the audit scheduler"""
    audit_scheduler.disable_scheduler()