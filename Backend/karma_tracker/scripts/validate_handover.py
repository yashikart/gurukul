#!/usr/bin/env python3
"""
Handover Validation Script

This script validates that all Day 4 deliverables have been successfully implemented.
"""

import os
import sys
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def validate_files_exist():
    """Validate that all required files exist"""
    print("=== FILE VALIDATION ===")
    
    required_files = [
        "utils/unreal_broadcast.py",
        "reports/unreal_simulation_log.json",
        "docs/HANDOVER_GUIDE.md",
        "system_manifest.json",
        "README.md"
    ]
    
    all_valid = True
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} does not exist")
            all_valid = False
    
    return all_valid

def validate_simulation_log():
    """Validate the simulation log content"""
    print("\n=== SIMULATION LOG VALIDATION ===")
    
    try:
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "reports/unreal_simulation_log.json")
        
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        
        # Check required fields
        required_fields = ["simulation_run", "num_players", "events", "summary"]
        missing_fields = [field for field in required_fields if field not in log_data]
        
        if missing_fields:
            print(f"❌ Missing fields in log: {missing_fields}")
            return False
        
        print(f"✅ Log contains required fields")
        print(f"✅ Simulation run at: {log_data['simulation_run']}")
        print(f"✅ Number of players: {log_data['num_players']}")
        print(f"✅ Total events generated: {len(log_data['events'])}")
        
        # Check summary
        if "total_events" in log_data["summary"]:
            print(f"✅ Summary total events: {log_data['summary']['total_events']}")
        else:
            print("❌ Missing total_events in summary")
            return False
            
        # Check event types
        expected_types = {"life_event", "death_event", "rebirth", "feedback_signal", "analytics"}
        actual_types = set(log_data["summary"]["event_types"].keys())
        
        if expected_types.issubset(actual_types):
            print("✅ All expected event types present")
            for event_type, count in log_data["summary"]["event_types"].items():
                print(f"  - {event_type}: {count} events")
        else:
            missing = expected_types - actual_types
            print(f"❌ Missing event types: {missing}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error validating simulation log: {e}")
        return False

def validate_manifest_version():
    """Validate that the manifest has been updated to v2.3"""
    print("\n=== MANIFEST VERSION VALIDATION ===")
    
    try:
        manifest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                   "system_manifest.json")
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        if manifest.get("version") == "2.3":
            print("✅ Manifest version updated to v2.3")
            return True
        else:
            print(f"❌ Manifest version is {manifest.get('version')}, expected 2.3")
            return False
            
    except Exception as e:
        print(f"❌ Error validating manifest: {e}")
        return False

def validate_readme_updates():
    """Validate that README.md has been updated with new sections"""
    print("\n=== README UPDATES VALIDATION ===")
    
    try:
        readme_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                 "README.md")
        
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Check for new features in key features section
        required_features = [
            "STP Bridge Integration",
            "Event Bus System",
            "Karmic Lifecycle Engine"
        ]
        
        missing_features = []
        for feature in required_features:
            if feature not in content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing features in README: {missing_features}")
            return False
        else:
            print("✅ All new features added to README key features")
        
        # Check for new sections
        required_sections = [
            "### STP Bridge Integration",
            "### Event Bus System",
            "### Karmic Lifecycle Engine"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ Missing sections in README: {missing_sections}")
            return False
        else:
            print("✅ All new sections added to README")
        
        # Check version update
        if "KarmaChain v2.3" in content:
            print("✅ README version updated to v2.3")
        else:
            print("❌ README version not updated")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error validating README: {e}")
        return False

def validate_handover_guide():
    """Validate that HANDOVER_GUIDE.md has been updated"""
    print("\n=== HANDOVER GUIDE VALIDATION ===")
    
    try:
        guide_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "docs/HANDOVER_GUIDE.md")
        
        # Open with utf-8 encoding to avoid character mapping issues
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for Unreal integration section
        if "Unreal Engine Integration" in content:
            print("✅ Unreal Engine Integration section added")
        else:
            print("❌ Missing Unreal Engine Integration section")
            return False
            
        # Check for deployment instructions
        if "Deployment Instructions" in content:
            print("✅ Deployment Instructions section added")
        else:
            print("❌ Missing Deployment Instructions section")
            return False
            
        # Check for new files in Unreal section
        required_files = [
            "/utils/unreal_broadcast.py",
            "/scripts/unreal_client_stub.py",
            "/scripts/unreal_simulation.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if file_path not in content:
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing file references in handover guide: {missing_files}")
            return False
        else:
            print("✅ All new file references added to handover guide")
            
        return True
        
    except Exception as e:
        print(f"❌ Error validating handover guide: {e}")
        return False

if __name__ == "__main__":
    print("Validating Day 4 - Unreal Integration Validation + Final Handover")
    print("=" * 70)
    
    # Run all validations
    files_valid = validate_files_exist()
    log_valid = validate_simulation_log()
    manifest_valid = validate_manifest_version()
    readme_valid = validate_readme_updates()
    guide_valid = validate_handover_guide()
    
    print("\n" + "=" * 70)
    print("FINAL VALIDATION RESULTS")
    print("=" * 70)
    
    all_valid = all([files_valid, log_valid, manifest_valid, readme_valid, guide_valid])
    
    if all_valid:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("✅ Unreal Integration Validation + Final Handover COMPLETE!")
        print("\nDeliverables successfully implemented:")
        print("  • /utils/unreal_broadcast.py - WebSocket push module")
        print("  • /reports/unreal_simulation_log.json - 10-player simulation report")
        print("  • Updated documentation (README.md, HANDOVER_GUIDE.md, system_manifest.json)")
        print("  • v2.3 manifest")
        sys.exit(0)
    else:
        print("❌ SOME VALIDATIONS FAILED!")
        print("Please check the implementation and run validation again.")
        sys.exit(1)