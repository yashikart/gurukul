"""
Quick test - just test one prompt to verify model works
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("Quick Model Test - Single Prompt")
print("=" * 50)

try:
    from local_model_service import get_local_model
    print("\n[1] Loading model...")
    model = get_local_model()
    
    print("[2] Loading into memory (this takes 1-2 minutes first time)...")
    model.ensure_loaded()
    
    if not model.is_loaded():
        print("[FAIL] Model not loaded!")
        sys.exit(1)
    
    print("[OK] Model loaded!")
    
    print("\n[3] Testing with Arabic prompt: 'مرحبا'")
    response = model.generate("مرحبا", max_new_tokens=50)
    print(f"\nResponse: {response}")
    
    print("\n[SUCCESS] Model is working!")
    
except Exception as e:
    print(f"\n[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

