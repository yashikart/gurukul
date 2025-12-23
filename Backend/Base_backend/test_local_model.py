"""
Test script for Local Arabic Model integration
Tests model loading, inference, and integration with LLMService
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set UTF-8 encoding for Windows
import io
import sys
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 60)
print("Testing Local Arabic Model Integration")
print("=" * 60)

# Test 1: Check dependencies
print("\n1️⃣ Testing Dependencies...")
try:
    import torch
    print(f"   [OK] PyTorch: {torch.__version__}")
    print(f"   [OK] CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   [OK] CUDA Device: {torch.cuda.get_device_name(0)}")
except ImportError as e:
    print(f"   [FAIL] PyTorch not installed: {e}")
    sys.exit(1)

try:
    import transformers
    print(f"   [OK] Transformers: {transformers.__version__}")
except ImportError as e:
    print(f"   [FAIL] Transformers not installed: {e}")
    sys.exit(1)

try:
    import peft
    print(f"   [OK] PEFT: {peft.__version__}")
except ImportError as e:
    print(f"   [FAIL] PEFT not installed: {e}")
    print("   [INFO] Run: pip install peft")
    sys.exit(1)

try:
    import bitsandbytes
    print(f"   [OK] BitsAndBytes: Available")
except ImportError as e:
    print(f"   [WARN] BitsAndBytes not installed: {e}")
    print("   [INFO] Run: pip install bitsandbytes")
    print("   [WARN] Note: Model will work but may use more memory without 4-bit quantization")

try:
    import accelerate
    print(f"   [OK] Accelerate: {accelerate.__version__}")
except ImportError as e:
    print(f"   [FAIL] Accelerate not installed: {e}")
    print("   [INFO] Run: pip install accelerate")
    sys.exit(1)

# Test 2: Check checkpoint files
print("\n2️⃣ Testing Checkpoint Files...")
# Try multiple possible paths
possible_paths = [
    Path(__file__).parent.parent.parent.parent / "checkpoints" / "checkpoint-100000",  # From nested Gurukul_new-main
    Path(__file__).parent.parent.parent / "checkpoints" / "checkpoint-100000",  # Direct from Backend
    Path(__file__).parent.parent.parent.parent.parent / "checkpoints" / "checkpoint-100000",  # From project root
]

checkpoint_path = None
for path in possible_paths:
    if (path / "adapter_model.safetensors").exists():
        checkpoint_path = path
        break

if checkpoint_path is None:
    # Use the first one as default and let the test fail with clear error
    checkpoint_path = possible_paths[0]

print(f"   Checkpoint path: {checkpoint_path}")

required_files = [
    "adapter_model.safetensors",
    "adapter_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "chat_template.jinja"
]

all_files_exist = True
for file_name in required_files:
    file_path = checkpoint_path / file_name
    if file_path.exists():
        size_mb = file_path.stat().st_size / (1024 * 1024)
        print(f"   [OK] {file_name} ({size_mb:.2f} MB)")
    else:
        print(f"   [FAIL] {file_name} - NOT FOUND")
        all_files_exist = False

if not all_files_exist:
    print("\n   [FAIL] Some checkpoint files are missing!")
    sys.exit(1)

# Test 3: Test local model service import
print("\n3️⃣ Testing Local Model Service Import...")
try:
    from local_model_service import LocalArabicModel, get_local_model
    print("   [OK] Local model service imported successfully")
except ImportError as e:
    print(f"   [FAIL] Failed to import local model service: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test LLMService integration
print("\n4️⃣ Testing LLMService Integration...")
try:
    from llm_service import LLMService
    print("   [OK] LLMService imported successfully")
    
    # Check if local model is available
    service = LLMService()
    if hasattr(service, 'local_model') and service.local_model is not None:
        print("   [OK] Local model instance created in LLMService")
    else:
        print("   [WARN] Local model not initialized (may be due to missing dependencies)")
    
    # Check providers list
    if 'local' in service.providers:
        print(f"   [OK] 'local' provider found in providers list: {service.providers}")
    else:
        print(f"   [FAIL] 'local' provider NOT in providers list: {service.providers}")
    
except Exception as e:
    print(f"   [FAIL] Failed to test LLMService: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test model initialization (without loading)
print("\n5️⃣ Testing Model Initialization (Dry Run)...")
try:
    model = get_local_model()
    print("   [OK] Model instance created")
    
    info = model.get_model_info()
    print(f"   Model Info:")
    for key, value in info.items():
        print(f"      {key}: {value}")
    
    print("\n   [INFO] Skipping actual model loading (would take time and memory)")
    print("   [INFO] To test full loading, run with: python test_local_model.py --load")
    
except Exception as e:
    print(f"   [FAIL] Failed to initialize model: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Test full model loading (if --load flag provided)
if "--load" in sys.argv:
    print("\n6. Testing Full Model Loading...")
    print("   [WARN] This will load the model into memory (may take 1-2 minutes)")
    try:
        model = get_local_model()
        model.ensure_loaded()
        
        if model.is_loaded():
            print("   [OK] Model loaded successfully!")
            
            # Test inference
            print("\n7. Testing Inference...")
            test_prompt = "Hello, how are you?"
            print(f"   Test prompt: {test_prompt}")
            
            response = model.generate(test_prompt, max_new_tokens=50)
            print(f"   [OK] Response received: {response[:100]}...")
        else:
            print("   [FAIL] Model failed to load")
            
    except Exception as e:
        print(f"   [FAIL] Failed to load model: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("[OK] Basic Integration Tests Complete!")
print("=" * 60)
print("\nNext Steps:")
print("   1. If all tests passed, the integration is ready")
print("   2. Start the backend server and test via API")
print("   3. Test from frontend by selecting 'Arabic Model'")
print("   4. Monitor logs for any runtime issues")
print("\n")

