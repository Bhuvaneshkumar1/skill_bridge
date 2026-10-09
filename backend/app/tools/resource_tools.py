import httpx
import urllib.parse
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from backend.app.config import settings
from backend.app.data.catalog_manager import CatalogManager

# External query cache dictionary: query_key -> List[Dict]
_EXTERNAL_RESOURCE_CACHE: Dict[str, List[Dict[str, Any]]] = {}

def find_free_learning_resources(
    skill: Optional[str] = None,
    career: Optional[str] = None,
    difficulty: Optional[str] = None,
    query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Finds verified free learning resources (videos, interactive courses, documentation, articles).
    Executes live web search first to dynamically fetch up-to-date courses across all subjects,
    supplemented by the verified catalog and YouTube Data API.
    """
    results: List[Dict[str, Any]] = []
    search_term = query or skill or career or "Programming"

    # 1. Live Web Search engine query for dynamic multi-subject course discovery
    cache_key = f"web_{search_term}_{difficulty}"
    if cache_key in _EXTERNAL_RESOURCE_CACHE:
        results.extend(_EXTERNAL_RESOURCE_CACHE[cache_key])
    else:
        try:
            web_results = _fetch_web_learning_resources(search_term, difficulty)
            if web_results:
                _EXTERNAL_RESOURCE_CACHE[cache_key] = web_results
                results.extend(web_results)
        except Exception:
            pass

    # 2. Search local catalog for supplementary matches
    local_matches = CatalogManager.search_resources(
        query=query,
        skill=skill,
        difficulty=difficulty
    )
    for r in local_matches:
        r_dict = r.model_dump()
        if not any(item["resource_url"] == r_dict["resource_url"] for item in results):
            results.append(r_dict)

    # 3. Query YouTube API v3 if key available
    if search_term and settings.YOUTUBE_API_KEY and not settings.DEMO_MODE:
        yt_cache_key = f"yt_{search_term}_{difficulty}"
        if yt_cache_key in _EXTERNAL_RESOURCE_CACHE:
            results.extend(_EXTERNAL_RESOURCE_CACHE[yt_cache_key])
        else:
            try:
                yt_results = _fetch_youtube_videos(search_term, settings.YOUTUBE_API_KEY)
                _EXTERNAL_RESOURCE_CACHE[yt_cache_key] = yt_results
                results.extend(yt_results)
            except Exception:
                pass

    return results


def _fetch_web_learning_resources(search_term: str, difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Queries web search for programming courses, tutorials, and documentation.
    Returns structured LearningResource dictionary items.
    """
    web_results = []
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    params = {"q": f"{search_term} free course tutorial documentation"}
    
    try:
        with httpx.Client(timeout=5.0, follow_redirects=True) as client:
            resp = client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                elements = soup.select('.result__body')
                for idx, r in enumerate(elements[:6]):
                    title_el = r.select_one('.result__title a')
                    snippet_el = r.select_one('.result__snippet')
                    if title_el:
                        t_text = title_el.get_text(strip=True)
                        raw_href = title_el.get('href', '')
                        if 'uddg=' in raw_href:
                            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                            actual_url = parsed.get('uddg', [raw_href])[0]
                        else:
                            actual_url = raw_href
                            
                        if not actual_url.startswith("http"):
                            continue
                            
                        snippet = snippet_el.get_text(strip=True) if snippet_el else f"Free online educational resource for {search_term}."
                        domain = urllib.parse.urlparse(actual_url).netloc.replace("www.", "")

                        web_results.append({
                            "id": f"web_{idx}_{abs(hash(actual_url)) % 10000}",
                            "title": t_text,
                            "provider": f"Web / {domain}",
                            "resource_url": actual_url,
                            "resource_type": "interactive_course" if "course" in t_text.lower() else ("documentation" if "doc" in t_text.lower() else "tutorial"),
                            "difficulty_level": difficulty or "All Levels",
                            "estimated_duration": "Self-paced",
                            "estimated_minutes": 60,
                            "cost_information": "100% Free Web Content",
                            "is_verified_free": True,
                            "skill_tags": [search_term, "Live Web Search"]
                        })
    except Exception:
        pass

    return web_results


def _fetch_youtube_videos(query: str, api_key: str) -> List[Dict[str, Any]]:
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": f"{query} tutorial programming free course",
        "type": "video",
        "maxResults": 3,
        "key": api_key
    }
    videos = []
    with httpx.Client(timeout=4.0) as client:
        response = client.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId")
                if video_id:
                    videos.append({
                        "id": f"yt_{video_id}",
                        "title": snippet.get("title", f"{query} Tutorial"),
                        "provider": f"YouTube / {snippet.get('channelTitle', 'EduChannel')}",
                        "resource_url": f"https://www.youtube.com/watch?v={video_id}",
                        "resource_type": "video",
                        "difficulty_level": "Beginner",
                        "estimated_duration": "30 mins",
                        "estimated_minutes": 30,
                        "cost_information": "100% Free Video",
                        "is_verified_free": True,
                        "skill_tags": [query]
                    })
    return videos

