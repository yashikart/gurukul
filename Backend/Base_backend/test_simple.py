"""
Simple test - tests model with one prompt
Shows progress and handles errors better
"""

import sys
import time
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

def safe_print(msg):
    """Print with immediate flush"""
    print(msg)
    try:
        sys.stdout.flush()
    except:
        pass

safe_print("=" * 60)
safe_print("Simple Arabic Model Test")
safe_print("=" * 60)
safe_print("")

try:
    safe_print("[1/4] Importing model service...")
    from local_model_service import get_local_model
    safe_print("      [OK] Imported")
    
    safe_print("\n[2/4] Creating model instance...")
    model = get_local_model()
    safe_print("      [OK] Instance created")
    
    safe_print("\n[3/4] Loading model (this may take 1-3 minutes)...")
    safe_print("      First time: Downloads ~2GB from HuggingFace")
    safe_print("      Subsequent: Loads from cache (faster)")
    safe_print("      Please wait...")
    
    start = time.time()
    model.ensure_loaded()
    elapsed = time.time() - start
    
    if model.is_loaded():
        safe_print(f"      [OK] Model loaded in {elapsed:.1f} seconds ({elapsed/60:.1f} min)")
    else:
        safe_print("      [FAIL] Model not loaded!")
        sys.exit(1)
    
    safe_print("\n[4/4] Testing inference...")
    safe_print("      Prompt: 'مرحبا' (Hello in Arabic)")
    
    start = time.time()
    response = model.generate("مرحبا", max_new_tokens=50, temperature=0.7)
    elapsed = time.time() - start
    
    safe_print(f"      [OK] Generated in {elapsed:.1f} seconds")
    safe_print("\n" + "-" * 60)
    safe_print("RESPONSE:")
    safe_print("-" * 60)
    safe_print(response)
    safe_print("-" * 60)
    
    safe_print("\n" + "=" * 60)
    safe_print("[SUCCESS] Model is working correctly!")
    safe_print("=" * 60)
    
except KeyboardInterrupt:
    safe_print("\n\n[INFO] Test interrupted by user")
    sys.exit(0)
except MemoryError as e:
    safe_print(f"\n[FAIL] Out of memory: {e}")
    safe_print("       Close other apps and try again")
    sys.exit(1)
except Exception as e:
    safe_print(f"\n[FAIL] Error: {type(e).__name__}: {e}")
    import traceback
    safe_print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)

