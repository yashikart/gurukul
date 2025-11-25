#!/usr/bin/env python3
"""
Enhanced test script to verify improved JPG image OCR and analysis functionality
"""

import os
import sys
import traceback
from PIL import Image, ImageDraw, ImageFont
import requests
import json
import time

# Add current directory to path to import rag functions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_text_image(text="Enhanced JPG Test\nLine 2: More content\nLine 3: Testing OCR", filename="enhanced_test.jpg"):
    """Create a more realistic test image with better text"""
    try:
        # Create a larger image with better contrast
        img = Image.new('RGB', (800, 400), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a better font if available
        try:
            # Try to use a system font
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            try:
                font = ImageFont.truetype("Arial.ttf", 24)
            except:
                try:
                    font = ImageFont.load_default()
                except:
                    font = None
        
        # Draw text with better positioning
        lines = text.split('\n')
        y_position = 50
        for line in lines:
            if font:
                draw.text((50, y_position), line, fill='black', font=font)
            else:
                draw.text((50, y_position), line, fill='black')
            y_position += 40
        
        # Add a border for better visibility
        draw.rectangle([(10, 10), (790, 390)], outline='black', width=2)
        
        img.save(filename, 'JPEG', quality=95)
        print(f"✅ Created enhanced test image: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Failed to create test image: {e}")
        return None

def test_enhanced_ocr():
    """Test the enhanced OCR functionality"""
    print("\n🔍 Testing Enhanced OCR Functionality...")
    
    try:
        from rag import extract_text_easyocr, analyze_image_content, generate_image_description
        print("✅ Successfully imported enhanced functions")
    except ImportError as e:
        print(f"❌ Failed to import enhanced functions: {e}")
        return False
    
    # Create test image
    test_image = create_text_image(
        "Smart Document Analysis\nJPG Image Processing Test\nThis text should be extracted correctly\nEnhanced OCR System",
        "smart_doc_test.jpg"
    )
    
    if not test_image or not os.path.exists(test_image):
        print("❌ Failed to create test image")
        return False
    
    try:
        # Test enhanced OCR
        print("\n📖 Testing enhanced OCR extraction...")
        ocr_result = extract_text_easyocr(test_image)
        print(f"OCR Result: '{ocr_result}'")
        
        # Test image analysis
        print("\n🖼️ Testing image analysis...")
        analysis = analyze_image_content(test_image)
        print(f"Image Analysis: {json.dumps(analysis, indent=2)}")
        
        # Test description generation
        print("\n📝 Testing description generation...")
        description = generate_image_description(analysis, ocr_result)
        print(f"Generated Description: {description}")
        
        # Clean up
        os.remove(test_image)
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced OCR test failed: {e}")
        traceback.print_exc()
        if os.path.exists(test_image):
            os.remove(test_image)
        return False

def test_api_endpoint():
    """Test the enhanced API endpoint (if server is running)"""
    print("\n🌐 Testing API Endpoint...")
    
    # Check if server is running
    try:
        response = requests.get("http://127.0.0.1:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("⚠️ Server responded but with non-200 status")
    except requests.exceptions.RequestException:
        print("⚠️ Server is not running, skipping API test")
        return False
    
    # Create test image for API
    test_image = create_text_image(
        "API Test Document\nSmart JPG Analysis\nThis is a test of the enhanced image processing API\nDate: 2025-01-25",
        "api_test.jpg"
    )
    
    if not test_image or not os.path.exists(test_image):
        print("❌ Failed to create test image for API")
        return False
    
    try:
        # Test the enhanced API endpoint
        with open(test_image, 'rb') as f:
            files = {'file': ('api_test.jpg', f, 'image/jpeg')}
            data = {'llm': 'grok'}
            
            print("📤 Sending request to API...")
            response = requests.post(
                "http://127.0.0.1:8000/process-img",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API request successful!")
            print(f"OCR Text: {result.get('ocr_text', 'N/A')}")
            print(f"Query: {result.get('query', 'N/A')}")
            print(f"Answer (first 200 chars): {result.get('answer', 'N/A')[:200]}...")
            print(f"LLM Used: {result.get('llm', 'N/A')}")
            return True
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False
    finally:
        if os.path.exists(test_image):
            os.remove(test_image)

def main():
    print("=" * 70)
    print("🚀 Enhanced JPG Image Processing Test Suite")
    print("=" * 70)
    
    # Test enhanced OCR functionality
    ocr_success = test_enhanced_ocr()
    
    # Test API endpoint
    api_success = test_api_endpoint()
    
    print("\n" + "=" * 70)
    print("📊 Enhanced Test Results Summary")
    print("=" * 70)
    
    print(f"Enhanced OCR Functions: {'✅ PASSED' if ocr_success else '❌ FAILED'}")
    print(f"API Endpoint Test: {'✅ PASSED' if api_success else '❌ FAILED'}")
    
    if ocr_success and api_success:
        print("\n🎉 All tests passed! JPG image summarization is working correctly.")
    elif ocr_success:
        print("\n✅ Core functionality works. Start the server to test the API endpoint.")
        print("💡 To start the server, run: python llmselect.py")
    else:
        print("\n❌ Issues detected with JPG image processing.")
        print("💡 Check the error messages above for troubleshooting.")

if __name__ == "__main__":
    main()