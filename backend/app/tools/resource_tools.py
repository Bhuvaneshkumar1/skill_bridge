import time
import logging
import httpx
import urllib.parse
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from backend.app.config import settings
from backend.app.data.catalog_manager import CatalogManager

logger = logging.getLogger(__name__)

class BoundedTTLCache:
    def __init__(self, maxsize: int = 100, ttl_seconds: int = 600):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[List[Dict[str, Any]]]:
        entry = self.cache.get(key)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            del self.cache[key]
            return None
        return entry["data"]

    def set(self, key: str, value: List[Dict[str, Any]]):
        if len(self.cache) >= self.maxsize:
            # Evict oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["created_at"])
            del self.cache[oldest_key]
        self.cache[key] = {
            "data": value,
            "created_at": time.time(),
            "expires_at": time.time() + self.ttl_seconds
        }

_RESOURCE_CACHE = BoundedTTLCache(maxsize=100, ttl_seconds=600)

REPUTABLE_EDUCATIONAL_CHANNELS: Dict[str, Dict[str, Any]] = {
    "cybersecurity": {
        "title": "NetworkChuck - Practical Cybersecurity & Network Defense",
        "provider": "YouTube / NetworkChuck",
        "channel_name": "NetworkChuck",
        "resource_url": "https://www.youtube.com/@NetworkChuck",
        "resource_type": "channel",
        "content_type": "channel",
        "language": "English",
        "difficulty_level": "All Levels",
        "estimated_duration": "Ongoing Channel",
        "estimated_minutes": 120,
        "cost_information": "100% Free on YouTube",
        "is_verified_free": True,
        "verification_status": "verified_channel",
        "skill_tags": ["Cybersecurity", "Networking", "Network Security", "Ethical Hacking"]
    },
    "web": {
        "title": "Traversy Media - Web Development & Modern Frameworks",
        "provider": "YouTube / Traversy Media",
        "channel_name": "Traversy Media",
        "resource_url": "https://www.youtube.com/@TraversyMedia",
        "resource_type": "channel",
        "content_type": "channel",
        "language": "English",
        "difficulty_level": "All Levels",
        "estimated_duration": "Ongoing Channel",
        "estimated_minutes": 120,
        "cost_information": "100% Free on YouTube",
        "is_verified_free": True,
        "verification_status": "verified_channel",
        "skill_tags": ["Web Development", "HTML5", "CSS3", "JavaScript", "React"]
    },
    "dsa": {
        "title": "NeetCode - Algorithms & Coding Interview Preparation",
        "provider": "YouTube / NeetCode",
        "channel_name": "NeetCode",
        "resource_url": "https://www.youtube.com/@NeetCode",
        "resource_type": "channel",
        "content_type": "channel",
        "language": "English",
        "difficulty_level": "Intermediate",
        "estimated_duration": "Ongoing Channel",
        "estimated_minutes": 180,
        "cost_information": "100% Free on YouTube",
        "is_verified_free": True,
        "verification_status": "verified_channel",
        "skill_tags": ["Data Structures", "Algorithms", "Interview Prep", "LeetCode"]
    },
    "python": {
        "title": "Corey Schafer - Python Programming Masterclasses",
        "provider": "YouTube / Corey Schafer",
        "channel_name": "Corey Schafer",
        "resource_url": "https://www.youtube.com/@coreyms",
        "resource_type": "channel",
        "content_type": "channel",
        "language": "English",
        "difficulty_level": "All Levels",
        "estimated_duration": "Ongoing Channel",
        "estimated_minutes": 240,
        "cost_information": "100% Free on YouTube",
        "is_verified_free": True,
        "verification_status": "verified_channel",
        "skill_tags": ["Python Fundamentals", "Object-Oriented Programming (OOP)", "Django", "Flask"]
    },
    "devops": {
        "title": "TechWorld with Nana - DevOps, Docker & Kubernetes",
        "provider": "YouTube / TechWorld with Nana",
        "channel_name": "TechWorld with Nana",
        "resource_url": "https://www.youtube.com/@TechWorldwithNana",
        "resource_type": "channel",
        "content_type": "channel",
        "language": "English",
        "difficulty_level": "Beginner",
        "estimated_duration": "Ongoing Channel",
        "estimated_minutes": 180,
        "cost_information": "100% Free on YouTube",
        "is_verified_free": True,
        "verification_status": "verified_channel",
        "skill_tags": ["DevOps", "Docker", "Kubernetes", "CI/CD", "Linux"]
    },
    "system design": {
        "title": "Hussein Nasser - Software Architecture & Database Systems",
        "provider": "YouTube / Hussein Nasser",
        "channel_name": "Hussein Nasser",
        "resource_url": "https://www.youtube.com/@hnasr",
        "resource_type": "channel",
        "content_type": "channel",
        "language": "English",
        "difficulty_level": "Intermediate",
        "estimated_duration": "Ongoing Channel",
        "estimated_minutes": 180,
        "cost_information": "100% Free on YouTube",
        "is_verified_free": True,
        "verification_status": "verified_channel",
        "skill_tags": ["System Design & Architecture", "Databases", "Distributed Systems", "Networking"]
    }
}

def find_free_learning_resources(
    skill: Optional[str] = None,
    career: Optional[str] = None,
    difficulty: Optional[str] = None,
    query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    YouTube-First Learning Resource Discovery Engine.
    1. Returns verified YouTube courses/playlists from curated catalog.
    2. Suggests verified educational channels for matching domains.
    3. Queries live YouTube Data API v3 when configured.
    4. Generates properly encoded YouTube search fallback when external discovery fails.
    5. Includes validated web resources when available.
    """
    results: List[Dict[str, Any]] = []
    search_term = query or skill or career or "Programming"
    search_lower = search_term.lower()

    # 1. Search local verified catalog first
    local_matches = CatalogManager.search_resources(
        query=query,
        skill=skill,
        career=career,
        difficulty=difficulty
    )
    for r in local_matches:
        r_dict = r.model_dump()
        if not any(item["resource_url"] == r_dict["resource_url"] for item in results):
            results.append(r_dict)

    # 2. Check curated reputable channels for recognized subjects
    for cat_key, ch_data in REPUTABLE_EDUCATIONAL_CHANNELS.items():
        if cat_key in search_lower or any(t.lower() in search_lower for t in ch_data.get("skill_tags", [])):
            if not any(item["resource_url"] == ch_data["resource_url"] for item in results):
                ch_copy = ch_data.copy()
                ch_copy["id"] = f"ch_{cat_key.replace(' ', '_')}"
                results.append(ch_copy)

    # 3. Live YouTube API v3 query if API key available and not in demo mode
    yt_items_found = False
    if search_term and settings.YOUTUBE_API_KEY and not settings.DEMO_MODE:
        yt_cache_key = f"yt_{search_term}_{difficulty}"
        cached_yt = _RESOURCE_CACHE.get(yt_cache_key)
        if cached_yt is not None:
            for item in cached_yt:
                if not any(r["resource_url"] == item["resource_url"] for r in results):
                    results.append(item)
                    yt_items_found = True
        else:
            try:
                yt_results = _fetch_youtube_videos(search_term, settings.YOUTUBE_API_KEY)
                if yt_results:
                    _RESOURCE_CACHE.set(yt_cache_key, yt_results)
                    for item in yt_results:
                        if not any(r["resource_url"] == item["resource_url"] for r in results):
                            results.append(item)
                            yt_items_found = True
            except Exception as err:
                logger.warning("YouTube API discovery failed for '%s': %s", search_term, str(err))

    # 4. Generate properly encoded YouTube search fallback if absent from catalog or external API failed
    # (Requirement 8: Generate properly encoded YouTube search URL without inventing fake IDs)
    encoded_search_query = urllib.parse.quote_plus(f"{search_term} full course tutorial")
    fallback_url = f"https://www.youtube.com/results?search_query={encoded_search_query}"
    if not any(item.get("resource_url") == fallback_url for item in results):
        results.append({
            "id": f"yt_fallback_{abs(hash(search_term)) % 100000}",
            "title": f"Explore YouTube Courses & Tutorials for '{search_term}'",
            "provider": "YouTube / Live Search Fallback",
            "channel_name": "YouTube Educational Community",
            "resource_url": fallback_url,
            "resource_type": "search_fallback",
            "content_type": "search_fallback",
            "language": "English",
            "difficulty_level": difficulty or "All Levels",
            "estimated_duration": "Self-paced",
            "estimated_minutes": 60,
            "cost_information": "Unverified Search Results (Free on YouTube)",
            "is_verified_free": False,
            "verification_status": "search_fallback",
            "skill_tags": [search_term, "YouTube Search Fallback"]
        })

    # 5. Live Web Search engine query with TTL Cache (retained for web discovery)
    cache_key = f"web_{search_term}_{difficulty}"
    cached_web = _RESOURCE_CACHE.get(cache_key)
    if cached_web is not None:
        for item in cached_web:
            if not any(r["resource_url"] == item["resource_url"] for r in results):
                results.append(item)
    else:
        try:
            web_results = _fetch_web_learning_resources(search_term, difficulty)
            if web_results:
                _RESOURCE_CACHE.set(cache_key, web_results)
                for item in web_results:
                    if not any(r["resource_url"] == item["resource_url"] for r in results):
                        results.append(item)
        except Exception as err:
            logger.warning("Web search resource discovery failed for '%s': %s", search_term, str(err))

    return results


def _fetch_web_learning_resources(search_term: str, difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Queries web search for programming courses, tutorials, and documentation.
    Web search results are explicitly marked with is_verified_free = False.
    """
    web_results = []
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    params = {"q": f"{search_term} free course tutorial documentation"}

    try:
        with httpx.Client(timeout=4.0, follow_redirects=True) as client:
            resp = client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                elements = soup.select('.result__body')
                for idx, r in enumerate(elements[:4]):
                    title_el = r.select_one('.result__title a')
                    if title_el:
                        t_text = title_el.get_text(strip=True)
                        raw_href = title_el.get('href', '')
                        if 'uddg=' in raw_href:
                            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                            actual_url = parsed.get('uddg', [raw_href])[0]
                        else:
                            actual_url = raw_href

                        # URL Validation
                        parsed_url = urllib.parse.urlparse(actual_url)
                        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
                            continue

                        domain = parsed_url.netloc.replace("www.", "")

                        web_results.append({
                            "id": f"web_{idx}_{abs(hash(actual_url)) % 10000}",
                            "title": t_text,
                            "provider": f"Web / {domain}",
                            "channel_name": domain,
                            "resource_url": actual_url,
                            "resource_type": "interactive_course" if "course" in t_text.lower() else ("documentation" if "doc" in t_text.lower() else "tutorial"),
                            "content_type": "website",
                            "language": "English",
                            "difficulty_level": difficulty or "All Levels",
                            "estimated_duration": "Self-paced",
                            "estimated_minutes": 60,
                            "cost_information": "Unverified Free Web Content",
                            "is_verified_free": False,
                            "verification_status": "unverified_search",
                            "skill_tags": [search_term, "Live Web Search"]
                        })
            else:
                logger.warning("Web search engine returned HTTP %d for query '%s'", resp.status_code, search_term)
    except Exception as err:
        logger.warning("Web search error for query '%s': %s", search_term, str(err))

    return web_results


def _fetch_youtube_videos(query: str, api_key: str) -> List[Dict[str, Any]]:
    """
    Live YouTube Data API v3 query.
    Extracts verified video, playlist, and channel items with real URLs.
    """
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": f"{query} tutorial programming course",
        "type": "video,playlist,channel",
        "maxResults": 4,
        "key": api_key
    }
    videos = []
    try:
        with httpx.Client(timeout=4.0) as client:
            response = client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    snippet = item.get("snippet", {})
                    id_obj = item.get("id", {})
                    channel_title = snippet.get("channelTitle", "YouTube Educator")

                    if id_obj.get("videoId"):
                        vid = id_obj["videoId"]
                        videos.append({
                            "id": f"yt_vid_{vid}",
                            "title": snippet.get("title", f"{query} Tutorial"),
                            "provider": f"YouTube / {channel_title}",
                            "channel_name": channel_title,
                            "resource_url": f"https://www.youtube.com/watch?v={vid}",
                            "resource_type": "video",
                            "content_type": "video",
                            "language": "English",
                            "difficulty_level": "Beginner",
                            "estimated_duration": "30 mins",
                            "estimated_minutes": 30,
                            "cost_information": "Free on YouTube (Live Discovery)",
                            "is_verified_free": False,
                            "verification_status": "discovered_video",
                            "skill_tags": [query, "YouTube Video"]
                        })
                    elif id_obj.get("playlistId"):
                        pid = id_obj["playlistId"]
                        videos.append({
                            "id": f"yt_pl_{pid}",
                            "title": snippet.get("title", f"{query} Course Playlist"),
                            "provider": f"YouTube / {channel_title}",
                            "channel_name": channel_title,
                            "resource_url": f"https://www.youtube.com/playlist?list={pid}",
                            "resource_type": "playlist",
                            "content_type": "playlist",
                            "language": "English",
                            "difficulty_level": "Beginner",
                            "estimated_duration": "Playlist",
                            "estimated_minutes": 180,
                            "cost_information": "Free on YouTube (Live Discovery)",
                            "is_verified_free": False,
                            "verification_status": "discovered_playlist",
                            "skill_tags": [query, "YouTube Playlist"]
                        })
                    elif id_obj.get("channelId"):
                        cid = id_obj["channelId"]
                        videos.append({
                            "id": f"yt_ch_{cid}",
                            "title": snippet.get("title", f"{channel_title} Channel"),
                            "provider": f"YouTube / {channel_title}",
                            "channel_name": channel_title,
                            "resource_url": f"https://www.youtube.com/channel/{cid}",
                            "resource_type": "channel",
                            "content_type": "channel",
                            "language": "English",
                            "difficulty_level": "All Levels",
                            "estimated_duration": "Channel",
                            "estimated_minutes": 60,
                            "cost_information": "Free on YouTube (Live Discovery)",
                            "is_verified_free": False,
                            "verification_status": "discovered_channel",
                            "skill_tags": [query, "YouTube Channel"]
                        })
            else:
                logger.warning("YouTube API returned HTTP %d for query '%s'", response.status_code, query)
    except Exception as err:
        logger.warning("YouTube search error for query '%s': %s", query, str(err))

    return videos
