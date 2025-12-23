"""
Direct test of YouTube API to verify it's working
"""
import requests
import os

# Get YouTube API key
youtube_api_key = os.getenv("YOUTUBE_API_KEY", "AIzaSyCJhsvlm7aAhnOBM6oBl1d90s9l67ksfbc")

# Test search
subject = "Biology"
topic = "Photosynthesis"
search_query = f"{topic} {subject} tutorial explanation"

search_url = "https://www.googleapis.com/youtube/v3/search"
params = {
    "part": "snippet",
    "q": search_query,
    "type": "video",
    "maxResults": 1,
    "order": "relevance",
    "key": youtube_api_key
}

print("Testing YouTube API directly")
print(f"Search query: {search_query}")
print(f"API Key (first 10 chars): {youtube_api_key[:10]}...")
print(f"URL: {search_url}")
print(f"Params: {params}")

try:
    response = requests.get(search_url, params=params, timeout=10)
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        print(f"Total results: {data.get('pageInfo', {}).get('totalResults', 0)}")
        print(f"Items count: {len(data.get('items', []))}")
        
        if data.get("items") and len(data["items"]) > 0:
            video = data["items"][0]
            video_id = video["id"]["videoId"]
            snippet = video["snippet"]
            print(f"\nFOUND VIDEO:")
            print(f"   Title: {snippet.get('title', 'Unknown')}")
            print(f"   Video ID: {video_id}")
            print(f"   Channel: {snippet.get('channelTitle', 'Unknown')}")
            print(f"   Embed URL: https://www.youtube.com/embed/{video_id}")
        else:
            print(f"\nNo videos found in response")
            print(f"   Response data: {data}")
    else:
        print(f"\nAPI Error: {response.status_code}")
        print(f"   Response text: {response.text[:500]}")
        try:
            error_data = response.json()
            if error_data.get("error"):
                error_info = error_data["error"]
                print(f"   Error code: {error_info.get('code', 'Unknown')}")
                print(f"   Error message: {error_info.get('message', 'Unknown')}")
                if error_info.get("errors"):
                    for err in error_info["errors"]:
                        print(f"   - {err.get('domain', '')}: {err.get('reason', '')} - {err.get('message', '')}")
        except:
            pass
            
except Exception as e:
    print(f"\nException: {str(e)}")
    import traceback
    traceback.print_exc()

