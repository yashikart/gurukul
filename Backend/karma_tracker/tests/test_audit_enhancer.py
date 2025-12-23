"""
Test suite for Audit Enhancer
"""
import sys
import os
import json
import tempfile
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.audit_enhancer import (
    AuditEnhancer, 
    enhance_single_entry, 
    create_daily_audit_snapshot,
    export_daily_audit_snapshot,
    auto_export_telemetry_feed,
    verify_ledger_entry_integrity,
    verify_snapshot_integrity
)

def test_hash_ledger_entry():
    """Test hashing of ledger entries"""
    enhancer = AuditEnhancer()
    
    # Test entry
    entry = {
        "event_id": "test_001",
        "event_type": "test_event",
        "data": {"value": 42},
        "timestamp": "2023-01-01T00:00:00Z"
    }
    
    # Hash the entry
    hash_value = enhancer.hash_ledger_entry(entry)
    
    # Check that we get a valid SHA-256 hash
    assert isinstance(hash_value, str)
    assert len(hash_value) == 64  # SHA-256 produces 64-character hex string
    assert all(c in '0123456789abcdef' for c in hash_value)
    
    # Check that the same entry produces the same hash
    hash_value2 = enhancer.hash_ledger_entry(entry)
    assert hash_value == hash_value2
    
    print("✓ Hash ledger entry test passed")

def test_add_block_references():
    """Test adding block references to ledger entries"""
    enhancer = AuditEnhancer()
    
    # Test entry
    entry = {
        "event_id": "test_002",
        "event_type": "test_event",
        "data": {"value": 100},
        "timestamp": "2023-01-01T00:00:00Z"
    }
    
    # Add block references
    enhanced_entry = enhancer.add_block_references(entry, 5, "previous_hash_123")
    
    # Check structure
    assert "_block_ref" in enhanced_entry
    block_ref = enhanced_entry["_block_ref"]
    assert block_ref["ledger_index"] == 5
    assert block_ref["previous_hash"] == "previous_hash_123"
    assert "timestamp" in block_ref
    assert "entry_hash" in block_ref
    assert isinstance(block_ref["entry_hash"], str)
    assert len(block_ref["entry_hash"]) == 64
    
    print("✓ Add block references test passed")

def test_enhance_ledger_entry():
    """Test enhancing ledger entries with cryptographic features"""
    enhancer = AuditEnhancer()
    
    # Test entry
    entry = {
        "event_id": "test_003",
        "event_type": "test_event",
        "data": {"value": 200},
        "timestamp": "2023-01-01T00:00:00Z"
    }
    
    # Enhance the entry
    enhanced_entry = enhancer.enhance_ledger_entry(entry, 10, "prev_hash_456")
    
    # Check structure
    assert "_block_ref" in enhanced_entry
    assert "_audit_hash" in enhanced_entry
    assert isinstance(enhanced_entry["_audit_hash"], str)
    assert len(enhanced_entry["_audit_hash"]) == 64
    
    # Verify integrity
    assert verify_ledger_entry_integrity(enhanced_entry)
    
    print("✓ Enhance ledger entry test passed")

def test_create_merkle_root():
    """Test creation of merkle root from hashes"""
    enhancer = AuditEnhancer()
    
    # Test with empty list
    root = enhancer._create_merkle_root([])
    assert isinstance(root, str)
    assert len(root) == 64
    
    # Test with single hash
    single_hash = "a" * 64
    root = enhancer._create_merkle_root([single_hash])
    assert root == single_hash
    
    # Test with multiple hashes
    hashes = ["a" * 64, "b" * 64, "c" * 64, "d" * 64]
    root = enhancer._create_merkle_root(hashes)
    assert isinstance(root, str)
    assert len(root) == 64
    
    print("✓ Create merkle root test passed")

def test_create_daily_snapshot():
    """Test creation of daily snapshots"""
    # Create snapshot
    snapshot = create_daily_audit_snapshot()
    
    # Check structure
    assert "snapshot_id" in snapshot
    assert "date" in snapshot
    assert "timestamp" in snapshot
    assert "entry_count" in snapshot
    assert "merkle_root" in snapshot
    assert "entries" in snapshot
    assert "version" in snapshot
    assert "snapshot_hash" in snapshot
    
    # Check types
    assert isinstance(snapshot["snapshot_id"], str)
    assert isinstance(snapshot["entry_count"], int)
    assert isinstance(snapshot["merkle_root"], str)
    assert isinstance(snapshot["entries"], list)
    
    # Verify integrity
    assert verify_snapshot_integrity(snapshot)
    
    print("✓ Create daily snapshot test passed")

def test_export_daily_snapshot():
    """Test exporting daily snapshots to file"""
    # Create temporary directory for export
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create enhancer with temporary directory
        enhancer = AuditEnhancer({"export_directory": temp_dir})
        
        # Export snapshot
        filepath = enhancer.export_daily_snapshot(filename="test_snapshot.json")
        
        # Check that file was created
        assert os.path.exists(filepath)
        
        # Check file content
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        assert "snapshot_id" in data
        assert "date" in data
        assert "entries" in data
        
        print("✓ Export daily snapshot test passed")

def test_auto_export_telemetry_feed():
    """Test auto-export of telemetry feed"""
    # Create temporary directory for export
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create enhancer with temporary directory
        enhancer = AuditEnhancer({
            "export_directory": temp_dir,
            "export_filename": "core_telemetry_bridge.json"
        })
        
        # Patch the global instance
        import utils.audit_enhancer
        utils.audit_enhancer.audit_enhancer = enhancer
        
        # Auto-export
        filepath = auto_export_telemetry_feed()
        
        # Check that file was created
        assert os.path.exists(filepath)
        
        # Check file content
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        assert "snapshot_id" in data
        assert "date" in data
        assert "entries" in data
        
        print("✓ Auto export telemetry feed test passed")

def test_verify_integrity():
    """Test integrity verification functions"""
    enhancer = AuditEnhancer()
    
    # Test entry
    entry = {
        "event_id": "test_004",
        "event_type": "test_event",
        "data": {"value": 300},
        "timestamp": "2023-01-01T00:00:00Z"
    }
    
    # Enhance the entry
    enhanced_entry = enhancer.enhance_ledger_entry(entry, 15, "prev_hash_789")
    
    # Verify integrity - should pass
    assert verify_ledger_entry_integrity(enhanced_entry)
    
    # Modify entry and verify - should fail
    modified_entry = enhanced_entry.copy()
    modified_entry["data"]["value"] = 999
    assert not verify_ledger_entry_integrity(modified_entry)
    
    # Test snapshot integrity
    snapshot = create_daily_audit_snapshot()
    
    # Verify integrity - should pass
    assert verify_snapshot_integrity(snapshot)
    
    # Modify snapshot and verify - should fail
    modified_snapshot = snapshot.copy()
    modified_snapshot["entry_count"] = 999
    assert not verify_snapshot_integrity(modified_snapshot)
    
    print("✓ Verify integrity test passed")

if __name__ == "__main__":
    print("Running Audit Enhancer Tests...")
    
    test_hash_ledger_entry()
    test_add_block_references()
    test_enhance_ledger_entry()
    test_create_merkle_root()
    test_create_daily_snapshot()
    test_export_daily_snapshot()
    test_auto_export_telemetry_feed()
    test_verify_integrity()
    
    print("\n🎉 All audit enhancer tests passed!")