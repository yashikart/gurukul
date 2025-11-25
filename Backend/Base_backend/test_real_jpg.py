#!/usr/bin/env python3
"""
Test JPG image processing with a real example
"""

import requests
import json
from PIL import Image, ImageDraw, ImageFont

def create_realistic_document():
    """Create a realistic document image for testing"""
    # Create a larger, more realistic document
    img = Image.new('RGB', (1200, 800), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to use a system font
        title_font = ImageFont.truetype("arial.ttf", 32)
        body_font = ImageFont.truetype("arial.ttf", 18)
    except:
        title_font = None
        body_font = None
    
    # Title
    draw.text((50, 50), "SMART DOCUMENT ANALYSIS", fill='black', font=title_font)
    draw.text((50, 100), "JPG Image Processing System", fill='blue', font=body_font)
    
    # Main content
    content = [
        "",
        "Document Overview:",
        "• This system processes JPG/JPEG images",
        "• Extracts text using advanced OCR technology", 
        "• Provides intelligent summarization",
        "• Supports multiple languages (English, Hindi)",
        "",
        "Key Features:",
        "1. High-quality text extraction",
        "2. Image analysis and description",
        "3. AI-powered content summarization",
        "4. Multiple LLM support (Groq, OpenAI, etc.)",
        "",
        "Technical Specifications:",
        "- Supported formats: JPG, JPEG, PNG",
        "- OCR Engine: EasyOCR with GPU acceleration",
        "- Image preprocessing and enhancement",
        "- Multi-language text recognition",
        "",
        "Date: January 25, 2025",
        "Status: Enhanced and Fully Operational"
    ]
    
    y_pos = 180
    for line in content:
        if line:
            draw.text((70, y_pos), line, fill='black', font=body_font)
        y_pos += 25
    
    # Add a border
    draw.rectangle([(20, 20), (1180, 780)], outline='black', width=3)
    
    # Save as high-quality JPG
    img.save("realistic_document.jpg", "JPEG", quality=95)
    print("✅ Created realistic document: realistic_document.jpg")
    return "realistic_document.jpg"

def test_jpg_processing():
    """Test the JPG processing with a realistic document"""
    print("🧪 Testing JPG Image Processing with Realistic Document")
    print("=" * 60)
    
    # Create test document
    test_file = create_realistic_document()
    
    try:
        # Test the API
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'image/jpeg')}
            data = {'llm': 'grok'}
            
            print("📤 Processing document through API...")
            response = requests.post(
                "http://127.0.0.1:8000/process-img",
                files=files,
                data=data,
                timeout=60
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Document processed successfully!")
            print("\n📄 OCR Results:")
            print("-" * 40)
            print(result.get('ocr_text', 'No text extracted'))
            
            print("\n🤖 AI Analysis:")
            print("-" * 40)
            answer = result.get('answer', 'No analysis provided')
            print(answer)
            
            print(f"\n🔧 Processing Details:")
            print(f"Query Type: {result.get('query', 'N/A')}")
            print(f"LLM Used: {result.get('llm', 'N/A')}")
            
            return True
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Clean up
        import os
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    success = test_jpg_processing()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 JPG Image Processing Test: PASSED")
        print("✅ Smart Document Analysis for JPG images is working correctly!")
    else:
        print("❌ JPG Image Processing Test: FAILED")
        print("💡 Check server status and API configuration")