"""
Quick test script to test the Arabic model with sample prompts
Tests 3 Arabic prompts and 2 English prompts
"""

import sys
import os
import time
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    import codecs
    try:
        # Set Windows console to UTF-8 code page
        import subprocess
        subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
    except:
        pass
    
    try:
        # Set UTF-8 for stdout and stderr
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        # Also set default encoding
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception as e:
        # If that fails, try setting environment variable
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        pass

# Force unbuffered output
try:
    sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None
except:
    pass  # If stdout is not reconfigurable, continue

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("Testing Arabic Model with Sample Prompts")
print("=" * 70)
print()

# Check memory availability
try:
    import psutil
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024**3)
    total_gb = mem.total / (1024**3)
    print(f"System Memory: {available_gb:.2f} GB available / {total_gb:.2f} GB total")
    if available_gb < 4:
        print("WARNING: Less than 4 GB RAM available. Model loading may fail!")
    print()
except ImportError:
    print("Note: psutil not available, cannot check memory")
    print()

# Import the model
model = None
try:
    print("[1/6] Importing model service...")
    from local_model_service import get_local_model
    print("[OK] Model service imported")
    
    print("\n[2/6] Creating model instance...")
    # Check CUDA availability first
    try:
        import torch
        if torch.cuda.is_available():
            print(f"      [INFO] CUDA detected! GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("      [WARN] CUDA not available - will use CPU (slow)")
    except ImportError:
        print("      [WARN] torch not available - cannot check CUDA status")
    except Exception as e:
        print(f"      [WARN] Could not check CUDA status: {e}")
    
    model = get_local_model()
    print("[OK] Model instance created")
    # Check device
    device_info = model.get_model_info()
    print(f"      Device: {device_info.get('device', 'unknown').upper()}")
    
    print("\n[3/6] Loading model into memory...")
    print("      This may take 1-3 minutes on CPU (first time downloads ~2GB)...")
    print("      Please be patient - the model is downloading/loading...")
    print("      Progress will be shown below:")
    sys.stdout.flush()
    
    start_time = time.time()
    
    # Wrap in try-except to catch any errors during loading
    try:
        # Add a timeout mechanism (but don't enforce it strictly)
        print("      Starting model loading process...")
        print("      [TIP] If this is the first run, downloading ~2GB may take 2-5 minutes")
        print("      [TIP] Watch for progress messages below...")
        sys.stdout.flush()
        
        # Add periodic heartbeat to show script is still running
        import threading
        heartbeat_stop = threading.Event()
        heartbeat_count = [0]  # Use list to allow modification from nested function
        
        def heartbeat():
            import time
            while not heartbeat_stop.is_set():
                time.sleep(10)
                heartbeat_count[0] += 1
                elapsed = heartbeat_count[0] * 10
                # Check if model is loaded, but don't rely on it exclusively
                try:
                    loaded = model.is_loaded()
                except:
                    loaded = False
                
                if not loaded:
                    print(f"      [STATUS] Still loading... ({elapsed}s elapsed - this is normal, please wait)")
                    sys.stdout.flush()
                else:
                    break
        
        heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        heartbeat_thread.start()
        print("      [INFO] Heartbeat started - you'll see status updates every 10 seconds")
        print("      [INFO] If you don't see heartbeat messages, the script may have crashed")
        sys.stdout.flush()
        
        try:
            model.ensure_loaded()
            heartbeat_stop.set()
        except KeyboardInterrupt:
            heartbeat_stop.set()
            print("\n      [INFO] Loading interrupted by user")
            raise
        except Exception as e:
            heartbeat_stop.set()
            print(f"\n      [ERROR] Exception during loading: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        load_time = time.time() - start_time
        
        if not model.is_loaded():
            print("\n[FAIL] Model instance exists but reports as not loaded!")
            print("       This might indicate a loading error.")
            sys.exit(1)
        
        print(f"\n[OK] Model loaded successfully!")
        print(f"     Total loading time: {load_time:.1f} seconds ({load_time/60:.1f} minutes)")
        sys.stdout.flush()
        
    except MemoryError as e:
        print(f"\n[FAIL] Out of memory error during model loading!")
        print(f"       Error: {e}")
        print("\n       Solutions:")
        print("       1. Close other applications to free up RAM")
        print("       2. The model needs ~4-6 GB RAM on CPU")
        print("       3. Consider using GPU if available")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n[INFO] Loading interrupted by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n[FAIL] Error during model loading!")
        print(f"       Error type: {type(e).__name__}")
        print(f"       Error message: {str(e)}")
        print("\n       Full traceback:")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
except ImportError as e:
    try:
        print(f"[FAIL] Failed to import model service: {e}", file=sys.stderr)
        print("\n       Make sure you're running this in the virtual environment!", file=sys.stderr)
        print("       Activate venv and try again:", file=sys.stderr)
        print("       > venv\\Scripts\\activate", file=sys.stderr)
        print("       > python test_model_prompts.py", file=sys.stderr)
    except:
        # If stdout is closed, write to stderr directly
        sys.stderr.write(f"[FAIL] Failed to import model service: {e}\n")
        sys.stderr.write("\n       Make sure you're running this in the virtual environment!\n")
        sys.stderr.write("       Activate venv: venv\\Scripts\\activate\n")
    sys.exit(1)
except Exception as e:
    print(f"[FAIL] Error initializing model: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test prompts
test_prompts = [
    # Arabic prompts
    {
        "prompt": "مرحبا، كيف حالك؟",
        "language": "Arabic",
        "description": "Greeting in Arabic"
    },
    {
        "prompt": "ما هو الذكاء الاصطناعي؟",
        "language": "Arabic",
        "description": "Question about AI in Arabic"
    },
    {
        "prompt": "اشرح لي كيف يعمل التعلم الآلي",
        "language": "Arabic",
        "description": "Request to explain machine learning in Arabic"
    },
    # English prompts (requesting Arabic responses)
    {
        "prompt": "Hello, how are you? Please answer in Arabic.",
        "language": "English",
        "description": "Simple greeting (requesting Arabic response)"
    },
    {
        "prompt": "What is artificial intelligence? Please answer in Arabic.",
        "language": "English",
        "description": "Question about AI (requesting Arabic response)"
    }
]

print("\n" + "=" * 70)
print("Starting Prompt Tests")
print("=" * 70)
print()

successful_tests = 0
failed_tests = 0

# Test each prompt
for i, test in enumerate(test_prompts, 1):
    print(f"[{i}/5] Test {i}: {test['language']} - {test['description']}")
    print("-" * 70)
    # Print Arabic text directly (encoding should be handled by UTF-8 setup above)
    print(f"Input: {test['prompt']}")
    print("Generating response... (this may take 10-30 seconds on CPU)")
    sys.stdout.flush()
    
    try:
        start_gen = time.time()
        response = model.generate(
            prompt=test['prompt'],
            max_new_tokens=150,
            temperature=0.7,
            top_p=0.9
        )
        gen_time = time.time() - start_gen
        
        print(f"\n[OK] Response received in {gen_time:.1f} seconds ({len(response)} characters):")
        print("-" * 70)
        # Print response directly (encoding handled by UTF-8 setup)
        print(response)
        print("-" * 70)
        successful_tests += 1
        
    except MemoryError as e:
        print(f"\n[FAIL] Out of memory during generation!")
        print(f"       Error: {e}")
        print("       Try reducing max_new_tokens or closing other applications")
        failed_tests += 1
        continue
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user (Ctrl+C)")
        print(f"\nCompleted {successful_tests} tests before interruption")
        sys.exit(0)
    except Exception as e:
        print(f"\n[FAIL] Error generating response!")
        print(f"       Error type: {type(e).__name__}")
        print(f"       Error message: {str(e)}")
        print("\n       Full traceback:")
        import traceback
        traceback.print_exc()
        failed_tests += 1
        continue
    
    print()  # Blank line between tests
    sys.stdout.flush()

print("\n" + "=" * 70)
print("Test Summary")
print("=" * 70)
print(f"Successful: {successful_tests}/5")
print(f"Failed: {failed_tests}/5")

if successful_tests == 5:
    print("\n[SUCCESS] All tests passed! Model is working correctly.")
    print("You can now use it in your application!")
elif successful_tests > 0:
    print(f"\n[PARTIAL] {successful_tests} tests passed, {failed_tests} failed.")
    print("Model is partially working. Check errors above.")
else:
    print("\n[FAIL] All tests failed. Check errors above for details.")

print("\n")
