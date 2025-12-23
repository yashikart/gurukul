"""
YouTube Link Helper
Detects YouTube link requests and appends actual YouTube search/video links
"""

import re
import logging
import urllib.parse
from typing import Optional, List

logger = logging.getLogger(__name__)

# Keywords that indicate YouTube link requests
YOUTUBE_KEYWORDS = [
    'youtube', 'youtu.be', 'video', 'videos', 'watch', 'channel',
    'link', 'links', 'رابط', 'روابط', 'فيديو', 'فيديوهات', 'يوتيوب',
    'give me', 'show me', 'find me', 'أعطني', 'أعرض لي', 'ابحث لي'
]

def detect_youtube_request(prompt: str) -> bool:
    """
    Detect if the user is asking for YouTube links
    
    Args:
        prompt: User's prompt text
        
    Returns:
        True if YouTube links are requested, False otherwise
    """
    prompt_lower = prompt.lower()
    
    # Check for YouTube-related keywords
    has_youtube_keyword = any(keyword in prompt_lower for keyword in YOUTUBE_KEYWORDS)
    
    # Check for link-related phrases
    link_phrases = [
        'give me link', 'show me link', 'find link', 'get link',
        'أعطني رابط', 'أعرض رابط', 'ابحث عن رابط'
    ]
    has_link_phrase = any(phrase in prompt_lower for phrase in link_phrases)
    
    return has_youtube_keyword or has_link_phrase


def extract_topic(prompt: str) -> Optional[str]:
    """
    Extract the topic/subject from the prompt
    
    Args:
        prompt: User's prompt text
        
    Returns:
        Extracted topic or None
    """
    # Remove common phrases
    cleaned = prompt.lower()
    
    # Remove common request phrases (more comprehensive)
    remove_phrases = [
        'i want to learn', 'give me', 'show me', 'find me', 'get me',
        'youtube', 'link', 'links', 'video', 'videos', 'channel', 'channels',
        'some', 'please', 'about', 'to', 'for', 'the', 'a', 'an',
        'أريد أن أتعلم', 'أعطني', 'أعرض لي', 'ابحث لي', 'رابط', 'فيديو', 'يوتيوب',
        'من فضلك', 'بعض', 'حول', 'إلى', 'ل'
    ]
    
    for phrase in remove_phrases:
        # Use word boundaries to avoid partial matches
        cleaned = re.sub(r'\b' + re.escape(phrase) + r'\b', '', cleaned, flags=re.IGNORECASE)
    
    # Remove punctuation and extra spaces
    cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Extract remaining meaningful words (2+ characters, not common words)
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    words = [w.strip() for w in cleaned.split() if len(w.strip()) > 1 and w.strip() not in common_words]
    
    if words:
        # Take first few meaningful words as topic (limit to 3 words for better search)
        topic = ' '.join(words[:3])  # Max 3 words for better YouTube search
        return topic.strip()
    
    return None


def generate_youtube_links(topic: str, language: str = 'en') -> List[dict]:
    """
    Generate YouTube search links for a given topic
    
    Args:
        topic: The topic/subject to search for
        language: Language code ('en' or 'ar')
        
    Returns:
        List of dictionaries with 'label' and 'url' keys
    """
    if not topic:
        return []
    
    # Clean topic for URL encoding
    search_query_encoded = urllib.parse.quote(topic)
    search_query_plus = topic.replace(' ', '+')
    
    links = []
    
    # Main search link
    main_url = f"https://www.youtube.com/results?search_query={search_query_encoded}"
    if language == 'ar':
        links.append({"label": f"البحث عن '{topic}'", "url": main_url})
    else:
        links.append({"label": f"Search for '{topic}'", "url": main_url})
    
    # Tutorial-specific search
    tutorial_query = f"{topic}+tutorial"
    tutorial_encoded = urllib.parse.quote(tutorial_query)
    tutorial_url = f"https://www.youtube.com/results?search_query={tutorial_encoded}"
    if language == 'ar':
        links.append({"label": f"دروس '{topic}'", "url": tutorial_url})
    else:
        links.append({"label": f"'{topic}' Tutorials", "url": tutorial_url})
    
    # Course-specific search
    course_query = f"{topic}+course"
    course_encoded = urllib.parse.quote(course_query)
    course_url = f"https://www.youtube.com/results?search_query={course_encoded}"
    if language == 'ar':
        links.append({"label": f"دورة '{topic}'", "url": course_url})
    else:
        links.append({"label": f"'{topic}' Course", "url": course_url})
    
    return links[:3]  # Return top 3 links


def append_youtube_links(response: str, prompt: str) -> str:
    """
    Append YouTube links to response if YouTube links are requested
    
    Args:
        response: Original AI response
        prompt: User's original prompt
        
    Returns:
        Response with YouTube links appended if applicable
    """
    # Check if YouTube links are requested
    if not detect_youtube_request(prompt):
        return response
    
    # Extract topic
    topic = extract_topic(prompt)
    
    if not topic:
        # Fallback: use the prompt itself
        topic = prompt[:50]  # First 50 chars
    
    # Detect language (simple check for Arabic characters)
    has_arabic = bool(re.search(r'[\u0600-\u06FF]', prompt))
    language = 'ar' if has_arabic else 'en'
    
    # Generate YouTube links
    links = generate_youtube_links(topic, language)
    
    if not links:
        return response
    
    # Append links to response
    separator = "\n\n" if response.strip() else ""
    
    if language == 'ar':
        links_section = f"{separator}**روابط يوتيوب للبحث عن '{topic}':**\n\n"
        for i, link_info in enumerate(links, 1):
            links_section += f"{i}. [{link_info['label']}]({link_info['url']})\n"
        links_section += "\nانقر على الروابط أعلاه للعثور على مقاطع الفيديو التعليمية."
    else:
        links_section = f"{separator}**YouTube Links for '{topic}':**\n\n"
        for i, link_info in enumerate(links, 1):
            links_section += f"{i}. [{link_info['label']}]({link_info['url']})\n"
        links_section += "\nClick on the links above to find educational videos."
    
    return response + links_section

