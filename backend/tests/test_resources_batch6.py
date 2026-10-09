import time
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.data.catalog_manager import CatalogManager
from backend.app.tools.resource_tools import find_free_learning_resources, BoundedTTLCache

client = TestClient(app)

def test_catalog_resource_search_filters():
    """Verify search filtering by skill, career, difficulty, and resource type."""
    # Filter by skill
    py_res = CatalogManager.search_resources(skill="Python")
    assert len(py_res) > 0
    assert all(any("python" in t.lower() for t in r.skill_tags) for r in py_res)

    # Filter by career
    career_res = CatalogManager.search_resources(career="Python Developer")
    assert len(career_res) > 0

    # Filter by difficulty
    beg_res = CatalogManager.search_resources(difficulty="Beginner")
    assert len(beg_res) > 0
    assert all(r.difficulty_level.lower() == "beginner" for r in beg_res)


def test_verified_vs_unverified_resource_status():
    """Local catalog items must be verified_free=True, while external search returns verified_free=False."""
    # Local catalog matches
    catalog_items = CatalogManager.search_resources(skill="Python")
    assert all(r.is_verified_free is True for r in catalog_items)

    # Live resource discovery search
    all_items = find_free_learning_resources(skill="Python")
    assert len(all_items) > 0

    web_items = [item for item in all_items if item["provider"].startswith("Web /")]
    for w in web_items:
        assert w["is_verified_free"] is False
        assert "Unverified" in w["cost_information"]


def test_bounded_ttl_cache():
    """Cache evicts expired items and respects maximum size bounds."""
    cache = BoundedTTLCache(maxsize=2, ttl_seconds=1)
    cache.set("key1", [{"title": "Course 1"}])
    cache.set("key2", [{"title": "Course 2"}])

    assert cache.get("key1") is not None
    assert cache.get("key2") is not None

    # Maxsize eviction test
    cache.set("key3", [{"title": "Course 3"}])
    assert len(cache.cache) == 2
    assert cache.get("key3") is not None

    # TTL Expiry test
    time.sleep(1.1)
    assert cache.get("key3") is None


def test_resources_api_endpoints():
    """GET and POST /api/resources support query, skill, career, difficulty filters."""
    # GET with career parameter
    res1 = client.get("/api/resources?career=Python%20Developer&difficulty=Beginner")
    assert res1.status_code == 200
    data1 = res1.json()
    assert len(data1) > 0

    # POST search
    res2 = client.post("/api/resources/search", json={
        "career": "Python Developer",
        "difficulty": "Beginner"
    })
    assert res2.status_code == 200
    assert len(res2.json()) > 0
