#!/usr/bin/env python3
"""
Test script to verify JPG image OCR functionality
"""

import os
import sys
import traceback
from PIL import Image
import numpy as np

# Add current directory to path to import rag functions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from rag import extract_text_easyocr
    print("✅ Successfully imported extract_text_easyocr from rag.py")
except ImportError as e:
    print(f"❌ Failed to import from rag.py: {e}")
    sys.exit(1)

def create_test_image(text="Hello World\nThis is a test image", filename="test_image.jpg"):
    """Create a simple test image with text for OCR testing"""
    try:
        # Create a simple image with text
        img = Image.new('RGB', (400, 200), color='white')
        
        # Try to add text using PIL (basic approach)
        try:
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            # Use default font
            draw.text((10, 50), text, fill='black')
            img.save(filename)
            print(f"✅ Created test image: {filename}")
            return filename
        except Exception as e:
            print(f"⚠️ Could not create text image: {e}")
            # Create a simple colored image instead
            img.save(filename)
            print(f"✅ Created simple test image: {filename}")
            return filename
    except Exception as e:
        print(f"❌ Failed to create test image: {e}")
        return None

def test_image_formats():
    """Test OCR with different image formats"""
    test_results = {}
    
    # Test with JPG
    print("\n🔍 Testing JPG format...")
    jpg_file = create_test_image("Sample JPG Text\nLine 2", "test.jpg")
    if jpg_file and os.path.exists(jpg_file):
        try:
            result = extract_text_easyocr(jpg_file)
            test_results['jpg'] = {'success': True, 'result': result}
            print(f"JPG OCR Result: '{result}'")
        except Exception as e:
            test_results['jpg'] = {'success': False, 'error': str(e)}
            print(f"❌ JPG OCR failed: {e}")
            traceback.print_exc()
        finally:
            if os.path.exists(jpg_file):
                os.remove(jpg_file)
    
    # Test with JPEG
    print("\n🔍 Testing JPEG format...")
    jpeg_file = create_test_image("Sample JPEG Text\nLine 2", "test.jpeg")
    if jpeg_file and os.path.exists(jpeg_file):
        try:
            result = extract_text_easyocr(jpeg_file)
            test_results['jpeg'] = {'success': True, 'result': result}
            print(f"JPEG OCR Result: '{result}'")
        except Exception as e:
            test_results['jpeg'] = {'success': False, 'error': str(e)}
            print(f"❌ JPEG OCR failed: {e}")
            traceback.print_exc()
        finally:
            if os.path.exists(jpeg_file):
                os.remove(jpeg_file)
    
    # Test with PNG
    print("\n🔍 Testing PNG format...")
    png_file = create_test_image("Sample PNG Text\nLine 2", "test.png")
    if png_file and os.path.exists(png_file):
        try:
            result = extract_text_easyocr(png_file)
            test_results['png'] = {'success': True, 'result': result}
            print(f"PNG OCR Result: '{result}'")
        except Exception as e:
            test_results['png'] = {'success': False, 'error': str(e)}
            print(f"❌ PNG OCR failed: {e}")
            traceback.print_exc()
        finally:
            if os.path.exists(png_file):
                os.remove(png_file)
    
    return test_results

def test_easyocr_directly():
    """Test EasyOCR directly without our wrapper function"""
    print("\n🔧 Testing EasyOCR directly...")
    try:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False)
        
        # Create a simple test image
        test_file = create_test_image("Direct Test Text", "direct_test.jpg")
        if test_file and os.path.exists(test_file):
            try:
                result = reader.readtext(test_file, detail=0)
                print(f"✅ Direct EasyOCR result: {result}")
                text = " ".join(result)
                print(f"✅ Joined text: '{text}'")
                return True
            except Exception as e:
                print(f"❌ Direct EasyOCR failed: {e}")
                traceback.print_exc()
                return False
            finally:
                if os.path.exists(test_file):
                    os.remove(test_file)
    except Exception as e:
        print(f"❌ Could not test EasyOCR directly: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 JPG Image OCR Test Suite")
    print("=" * 60)
    
    # Test EasyOCR directly first
    direct_success = test_easyocr_directly()
    
    # Test our wrapper function
    test_results = test_image_formats()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    print(f"Direct EasyOCR test: {'✅ PASSED' if direct_success else '❌ FAILED'}")
    
    for format_name, result in test_results.items():
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"{format_name.upper()} format: {status}")
        if not result['success']:
            print(f"  Error: {result['error']}")
        elif result['result'].strip():
            print(f"  Extracted: '{result['result']}'")
        else:
            print(f"  ⚠️ No text extracted (might be blank image)")
    
    # Check if JPG specifically is working
    jpg_working = test_results.get('jpg', {}).get('success', False)
    if not jpg_working:
        print("\n❌ JPG processing is NOT working!")
        print("💡 Potential issues to investigate:")
        print("   - EasyOCR installation problems")
        print("   - OpenCV compatibility issues")
        print("   - PIL/Pillow image format support")
        print("   - File path or permissions issues")
    else:
        print("\n✅ JPG processing is working correctly!")

if __name__ == "__main__":
    main()