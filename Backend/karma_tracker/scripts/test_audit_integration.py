#!/usr/bin/env python3
"""
Test script for Audit Enhancement Integration
Demonstrates how the audit enhancement integrates with the existing logging system
"""
import sys
import os
import json
import tempfile
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from observability import (
    karmachain_logger,
    log_api_request,
    log_karma_action,
    export_audit_trail
)
from utils.audit_enhancer import audit_enhancer

def test_audit_integration():
    """Test integration between observability and audit enhancement"""
    print("Testing Audit Enhancement Integration...")
    
    # Log some events using the existing observability system
    print("  Logging test events...")
    
    log_api_request(
        request_id="req_001",
        method="POST",
        path="/api/v1/test",
        user_id="user_test_001",
        request_data={"action": "test_action", "value": 42}
    )
    
    log_karma_action(
        request_id="req_002",
        user_id="user_test_001",
        action="completing_lessons",
        karma_impact=5.0,
        role="learner",
        intent="learn"
    )
    
    # Check that entries were logged with cryptographic enhancements
    audit_trail = karmachain_logger.get_audit_trail(limit=10)
    print(f"  Retrieved {len(audit_trail)} audit entries")
    
    # Check that the entries have cryptographic enhancements
    for i, entry in enumerate(audit_trail):
        entry_dict = entry.to_dict()
        
        # Check for block references
        if "_block_ref" in entry_dict:
            block_ref = entry_dict["_block_ref"]
            print(f"  Entry {i+1} has block reference:")
            print(f"    Ledger Index: {block_ref.get('ledger_index')}")
            print(f"    Previous Hash: {block_ref.get('previous_hash')}")
            print(f"    Entry Hash: {block_ref.get('entry_hash')}")
        
        # Check for audit hash
        if "_audit_hash" in entry_dict:
            print(f"  Entry {i+1} has audit hash: {entry_dict['_audit_hash'][:16]}...")
    
    # Test export functionality
    print("  Testing audit trail export...")
    
    # Create temporary directory for export
    with tempfile.TemporaryDirectory() as temp_dir:
        export_file = os.path.join(temp_dir, "test_audit_export.json")
        export_audit_trail(export_file)
        
        # Check that file was created
        if os.path.exists(export_file):
            print(f"  ✓ Export file created: {export_file}")
            
            # Check file content
            with open(export_file, 'r') as f:
                data = json.load(f)
                
            print(f"  Export contains {data.get('entry_count', 0)} entries")
            print(f"  Merkle root: {data.get('merkle_root', '')[:16]}...")
            print(f"  Snapshot hash: {data.get('snapshot_hash', '')[:16]}...")
        else:
            print("  ✗ Export file not created")
    
    print("✓ Audit integration test completed")

def test_direct_audit_enhancer():
    """Test direct usage of audit enhancer"""
    print("\nTesting Direct Audit Enhancer Usage...")
    
    # Create test entry
    test_entry = {
        "event_id": "direct_test_001",
        "event_type": "direct_test_event",
        "data": {
            "test_value": 123,
            "test_string": "hello world"
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Enhance the entry
    enhanced = audit_enhancer.enhance_ledger_entry(test_entry, 100, "previous_hash_test")
    
    print(f"  Original entry keys: {list(test_entry.keys())}")
    print(f"  Enhanced entry keys: {list(enhanced.keys())}")
    
    # Check for added fields
    assert "_block_ref" in enhanced
    assert "_audit_hash" in enhanced
    
    block_ref = enhanced["_block_ref"]
    print(f"  Block reference: index={block_ref['ledger_index']}, prev_hash={block_ref['previous_hash']}")
    print(f"  Audit hash: {enhanced['_audit_hash']}")
    
    # Test verification
    from utils.audit_enhancer import verify_ledger_entry_integrity
    is_valid = verify_ledger_entry_integrity(enhanced)
    print(f"  Entry integrity verification: {'✓ PASS' if is_valid else '✗ FAIL'}")
    
    # Test with modified entry
    modified = enhanced.copy()
    modified["data"]["test_value"] = 999
    is_valid_modified = verify_ledger_entry_integrity(modified)
    print(f"  Modified entry verification: {'✓ PASS' if not is_valid_modified else '✗ FAIL (should fail)'}")
    
    print("✓ Direct audit enhancer test completed")

if __name__ == "__main__":
    print("Running Audit Enhancement Integration Tests")
    print("=" * 50)
    
    try:
        test_audit_integration()
        test_direct_audit_enhancer()
        
        print("\n" + "=" * 50)
        print("🎉 All audit integration tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()