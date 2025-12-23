"""
Test script for converting English sentences to Arabic using the checkpoint model
"""

import sys
import os
from pathlib import Path

# Add Backend/Base_backend to path to import local_model_service
backend_path = Path(__file__).parent / "Backend" / "Base_backend"
sys.path.insert(0, str(backend_path))

try:
    from local_model_service import get_local_model
    import torch
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure you have installed the required dependencies:")
    print("  pip install torch transformers peft bitsandbytes accelerate")
    sys.exit(1)


def convert_to_arabic(sentence: str, checkpoint_path: str = None) -> str:
    """
    Convert an English sentence to Arabic using the checkpoint model
    
    Args:
        sentence: English sentence to convert
        checkpoint_path: Optional path to checkpoint directory
        
    Returns:
        Arabic translation of the sentence
    """
    try:
        # Get the local Arabic model instance
        print(f"Loading Arabic model...")
        model = get_local_model(checkpoint_path)
        
        # Ensure model is loaded
        model.ensure_loaded()
        
        if not model.is_loaded():
            raise RuntimeError("Model failed to load. Please check checkpoint path.")
        
        print(f"Model loaded successfully!")
        print(f"Device: {model.device}")
        print(f"Model info: {model.get_model_info()}")
        print("-" * 60)
        
        # Create a translation prompt
        translation_prompt = f"""Translate the following English sentence to Arabic. 
Provide only the Arabic translation without any additional text or explanation.

English: {sentence}

Arabic:"""
        
        print(f"Input sentence: {sentence}")
        print(f"Generating Arabic translation...")
        print("-" * 60)
        
        # Generate Arabic translation
        arabic_translation = model.generate(
            prompt=translation_prompt,
            max_new_tokens=256,
            temperature=0.7,
            top_p=0.9
        )
        
        # Clean up the response (remove any extra formatting)
        arabic_translation = arabic_translation.strip()
        
        # Remove common prefixes that might be added
        prefixes_to_remove = [
            "Arabic:",
            "الترجمة:",
            "Translation:",
            "الترجمة العربية:"
        ]
        for prefix in prefixes_to_remove:
            if arabic_translation.startswith(prefix):
                arabic_translation = arabic_translation[len(prefix):].strip()
        
        return arabic_translation
        
    except Exception as e:
        print(f"Error during translation: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_single_sentence(sentence: str, checkpoint_path: str = None):
    """Test converting a single sentence"""
    print("=" * 60)
    print("ARABIC TRANSLATION TEST")
    print("=" * 60)
    print()
    
    try:
        arabic_result = convert_to_arabic(sentence, checkpoint_path)
        
        print()
        print("=" * 60)
        print("RESULT:")
        print("=" * 60)
        print(f"English: {sentence}")
        print(f"Arabic:  {arabic_result}")
        print("=" * 60)
        
        return arabic_result
        
    except Exception as e:
        print(f"❌ Translation failed: {e}")
        return None


def test_multiple_sentences(sentences: list, checkpoint_path: str = None):
    """Test converting multiple sentences"""
    print("=" * 60)
    print("BATCH ARABIC TRANSLATION TEST")
    print("=" * 60)
    print()
    
    results = []
    
    for i, sentence in enumerate(sentences, 1):
        print(f"\n[{i}/{len(sentences)}] Processing: {sentence}")
        print("-" * 60)
        
        try:
            arabic_result = convert_to_arabic(sentence, checkpoint_path)
            results.append({
                "english": sentence,
                "arabic": arabic_result,
                "success": True
            })
            print(f"✅ Success: {arabic_result}")
        except Exception as e:
            print(f"❌ Failed: {e}")
            results.append({
                "english": sentence,
                "arabic": None,
                "success": False,
                "error": str(e)
            })
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for i, result in enumerate(results, 1):
        if result["success"]:
            print(f"\n{i}. English: {result['english']}")
            print(f"   Arabic:  {result['arabic']}")
        else:
            print(f"\n{i}. English: {result['english']}")
            print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
    
    return results


if __name__ == "__main__":
    # Default checkpoint path (adjust if needed)
    # The model will auto-detect the checkpoint if it's in the standard location
    checkpoint_path = None
    
    # You can specify a custom checkpoint path here:
    # checkpoint_path = "checkpoints/checkpoint-100000"
    # Or use environment variable:
    # checkpoint_path = os.getenv("LOCAL_MODEL_CHECKPOINT_PATH")
    
    # Test sentences
    test_sentences = [
        "Hello, how are you?",
        "What is the weather today?",
        "I am learning Arabic language.",
        "Thank you for your help.",
        "Can you explain this concept to me?"
    ]
    
    # Check if command line argument provided
    if len(sys.argv) > 1:
        # Single sentence from command line
        sentence = " ".join(sys.argv[1:])
        test_single_sentence(sentence, checkpoint_path)
    else:
        # Test with default sentences
        print("No sentence provided. Testing with default sentences...")
        print()
        
        # Test single sentence first
        print("Testing single sentence conversion:")
        test_single_sentence(test_sentences[0], checkpoint_path)
        
        print("\n\n")
        
        # Test multiple sentences
        print("Testing batch conversion:")
        test_multiple_sentences(test_sentences, checkpoint_path)

