"""
Audit Enhancer Module

Adds SHA-256 hashing for every ledger entry, stores block references, and enables
daily cryptographic snapshot exports for verifiable telemetry.
"""
import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from database import karma_events_col
import logging

# Setup logging
logger = logging.getLogger(__name__)

class AuditEnhancer:
    """Enhances audit trail with cryptographic hashing and block references"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the audit enhancer"""
        self.config = config or {}
        self.export_directory = self.config.get("export_directory", "./exports")
        self.export_filename = self.config.get("export_filename", "core_telemetry_bridge.json")
        self.ledger_collection = karma_events_col  # Default to karma_events collection
        
        # Create export directory if it doesn't exist
        os.makedirs(self.export_directory, exist_ok=True)
        
    def hash_ledger_entry(self, entry: Dict[str, Any]) -> str:
        """
        Create SHA-256 hash of a ledger entry
        
        Args:
            entry: Ledger entry to hash
            
        Returns:
            SHA-256 hash as hex string
        """
        # Sort keys for consistent hashing
        entry_str = json.dumps(entry, sort_keys=True, default=str)
        entry_bytes = entry_str.encode('utf-8')
        return hashlib.sha256(entry_bytes).hexdigest()
    
    def add_block_references(self, entry: Dict[str, Any], 
                           ledger_index: int, 
                           previous_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        Add block references to a ledger entry
        
        Args:
            entry: Original ledger entry
            ledger_index: Position in the ledger
            previous_hash: Hash of the previous entry
            
        Returns:
            Enhanced entry with block references
        """
        enhanced_entry = entry.copy()
        enhanced_entry["_block_ref"] = {
            "ledger_index": ledger_index,
            "previous_hash": previous_hash,
            "timestamp": datetime.utcnow().isoformat(),
            "entry_hash": self.hash_ledger_entry(entry)
        }
        return enhanced_entry
    
    def enhance_ledger_entry(self, entry: Dict[str, Any], 
                           ledger_index: int, 
                           previous_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhance a ledger entry with cryptographic hash and block references
        
        Args:
            entry: Original ledger entry
            ledger_index: Position in the ledger
            previous_hash: Hash of the previous entry
            
        Returns:
            Cryptographically enhanced ledger entry
        """
        # Add block references
        enhanced_entry = self.add_block_references(entry, ledger_index, previous_hash)
        
        # Add SHA-256 hash of the entire enhanced entry
        enhanced_entry["_audit_hash"] = self.hash_ledger_entry(enhanced_entry)
        
        return enhanced_entry
    
    def get_daily_entries(self, date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get all ledger entries for a specific date
        
        Args:
            date: Date to filter entries (defaults to today)
            
        Returns:
            List of ledger entries for the specified date
        """
        if date is None:
            date = datetime.utcnow()
            
        # Get start and end of the day
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # Query entries for the day
        entries = list(self.ledger_collection.find({
            "timestamp": {
                "$gte": start_of_day,
                "$lt": end_of_day
            }
        }).sort("timestamp", 1))
        
        return entries
    
    def create_daily_snapshot(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Create a daily cryptographic snapshot of ledger entries
        
        Args:
            date: Date for the snapshot (defaults to today)
            
        Returns:
            Dict containing the snapshot with cryptographic proofs
        """
        if date is None:
            date = datetime.utcnow()
            
        # Get entries for the day
        entries = self.get_daily_entries(date)
        
        # Enhance entries with cryptographic hashes and block references
        enhanced_entries = []
        previous_hash = None
        
        for i, entry in enumerate(entries):
            enhanced_entry = self.enhance_ledger_entry(entry, i, previous_hash)
            enhanced_entries.append(enhanced_entry)
            previous_hash = enhanced_entry["_audit_hash"]
        
        # Create merkle root hash of all entry hashes
        entry_hashes = [entry["_audit_hash"] for entry in enhanced_entries]
        merkle_root = self._create_merkle_root(entry_hashes)
        
        # Create snapshot metadata
        snapshot = {
            "snapshot_id": hashlib.sha256(f"{date.isoformat()}{merkle_root}".encode()).hexdigest(),
            "date": date.date().isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
            "entry_count": len(enhanced_entries),
            "merkle_root": merkle_root,
            "entries": enhanced_entries,
            "version": "1.0"
        }
        
        # Add snapshot hash
        snapshot["snapshot_hash"] = self.hash_ledger_entry(snapshot)
        
        return snapshot
    
    def _create_merkle_root(self, hashes: List[str]) -> str:
        """
        Create a merkle root from a list of hashes
        
        Args:
            hashes: List of hashes
            
        Returns:
            Merkle root hash
        """
        if not hashes:
            return hashlib.sha256(b"empty").hexdigest()
            
        if len(hashes) == 1:
            return hashes[0]
            
        # Pairwise hash until we get a single hash
        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                # If odd number of hashes, duplicate the last one
                hashes.append(hashes[-1])
                
            new_hashes = []
            for i in range(0, len(hashes), 2):
                # Concatenate and hash pairs
                pair = hashes[i] + hashes[i+1]
                new_hash = hashlib.sha256(pair.encode()).hexdigest()
                new_hashes.append(new_hash)
                
            hashes = new_hashes
            
        return hashes[0]
    
    def export_daily_snapshot(self, date: Optional[datetime] = None, 
                            filename: Optional[str] = None) -> str:
        """
        Export daily snapshot to a JSON file
        
        Args:
            date: Date for the snapshot (defaults to today)
            filename: Override export filename
            
        Returns:
            Path to the exported file
        """
        # Create snapshot
        snapshot = self.create_daily_snapshot(date)
        
        # Determine filename
        if filename is None:
            date_str = (date or datetime.utcnow()).date().isoformat()
            filename = f"daily_snapshot_{date_str}.json"
            
        # Full path
        filepath = os.path.join(self.export_directory, filename)
        
        # Export to file
        try:
            with open(filepath, 'w') as f:
                json.dump(snapshot, f, indent=2, default=str)
                
            logger.info(f"Daily snapshot exported to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting daily snapshot: {str(e)}")
            raise
    
    def auto_export_daily_feed(self) -> str:
        """
        Auto-export daily feed to core telemetry bridge file
        
        Returns:
            Path to the exported file
        """
        filepath = os.path.join(self.export_directory, self.export_filename)
        return self.export_daily_snapshot(filename=self.export_filename)
    
    def verify_entry_integrity(self, entry: Dict[str, Any]) -> bool:
        """
        Verify the integrity of a ledger entry
        
        Args:
            entry: Entry to verify
            
        Returns:
            True if entry is valid, False otherwise
        """
        if "_audit_hash" not in entry:
            return False
            
        # Recalculate hash
        entry_copy = entry.copy()
        stored_hash = entry_copy.pop("_audit_hash", None)
        calculated_hash = self.hash_ledger_entry(entry_copy)
        
        return stored_hash == calculated_hash
    
    def verify_snapshot_integrity(self, snapshot: Dict[str, Any]) -> bool:
        """
        Verify the integrity of a snapshot
        
        Args:
            snapshot: Snapshot to verify
            
        Returns:
            True if snapshot is valid, False otherwise
        """
        if "snapshot_hash" not in snapshot:
            return False
            
        # Recalculate hash
        snapshot_copy = snapshot.copy()
        stored_hash = snapshot_copy.pop("snapshot_hash", None)
        calculated_hash = self.hash_ledger_entry(snapshot_copy)
        
        return stored_hash == calculated_hash

# Global instance
audit_enhancer = AuditEnhancer()

# Convenience functions
def enhance_single_entry(entry: Dict[str, Any], ledger_index: int, 
                        previous_hash: Optional[str] = None) -> Dict[str, Any]:
    """Enhance a single ledger entry"""
    return audit_enhancer.enhance_ledger_entry(entry, ledger_index, previous_hash)

def create_daily_audit_snapshot(date: Optional[datetime] = None) -> Dict[str, Any]:
    """Create a daily audit snapshot"""
    return audit_enhancer.create_daily_snapshot(date)

def export_daily_audit_snapshot(date: Optional[datetime] = None, 
                               filename: Optional[str] = None) -> str:
    """Export daily audit snapshot to file"""
    return audit_enhancer.export_daily_snapshot(date, filename)

def auto_export_telemetry_feed() -> str:
    """Auto-export daily telemetry feed"""
    return audit_enhancer.auto_export_daily_feed()

def verify_ledger_entry_integrity(entry: Dict[str, Any]) -> bool:
    """Verify integrity of a ledger entry"""
    return audit_enhancer.verify_entry_integrity(entry)

def verify_snapshot_integrity(snapshot: Dict[str, Any]) -> bool:
    """Verify integrity of a snapshot"""
    return audit_enhancer.verify_snapshot_integrity(snapshot)