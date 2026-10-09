import urllib.parse
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.data.catalog_manager import CatalogManager
from backend.app.tools.resource_tools import find_free_learning_resources

client = TestClient(app)

def test_all_catalog_resources_have_youtube_destinations():
    """Requirement 1 & 2: Every catalog course must direct to a verified YouTube destination."""
    resources = CatalogManager.get_resources()
    assert len(resources) > 0

    for r in resources:
        url = r.get("resource_url", "")
        assert "youtube.com" in url or "youtu.be" in url, f"Resource '{r.get('title')}' is not a YouTube URL: {url}"
        assert r.get("is_verified_free") is True
        assert r.get("verification_status") in ("verified_video", "verified_playlist", "verified_channel")
        assert r.get("channel_name") is not None and len(r.get("channel_name")) > 0
        assert r.get("language") == "English"
        assert r.get("content_type") in ("video", "playlist", "channel")

def test_reputable_channel_discovery_for_domain_topics():
    """Requirement 5: Prefer reputable educational channels for recognized domains."""
    # Cybersecurity search
    sec_results = find_free_learning_resources(query="cybersecurity")
    assert len(sec_results) > 0
    # Must include a verified cybersecurity channel or video
    channel_matches = [r for r in sec_results if r.get("verification_status") == "verified_channel"]
    assert len(channel_matches) > 0
    assert any("NetworkChuck" in c.get("channel_name", "") for c in channel_matches)

def test_unknown_topic_produces_valid_youtube_search_fallback():
    """Requirement 3 & 8: Absent subjects produce properly encoded YouTube search fallback without fabricated IDs."""
    unknown_query = "Quantum Computing and Qubits"
    results = find_free_learning_resources(query=unknown_query)
    assert len(results) > 0

    # Look for search fallback
    fallback_items = [r for r in results if r.get("verification_status") == "search_fallback"]
    assert len(fallback_items) > 0
    fb = fallback_items[0]

    assert "youtube.com/results?search_query=" in fb["resource_url"]
    assert fb["is_verified_free"] is False
    assert fb["content_type"] == "search_fallback"
    # Ensure no fabricated video ID (e.g., watch?v=)
    assert "watch?v=" not in fb["resource_url"]
    # Ensure proper URL encoding
    expected_encoded = urllib.parse.quote_plus(f"{unknown_query} full course tutorial")
    assert expected_encoded in fb["resource_url"]

def test_resources_api_youtube_fields_exposed():
    """Requirement 6: API responses expose channel_name, content_type, language, and verification_status."""
    res = client.get("/api/resources?query=Python")
    assert res.status_code == 200
    items = res.json()
    assert len(items) > 0

    sample = items[0]
    assert "channel_name" in sample
    assert "content_type" in sample
    assert "language" in sample
    assert "verification_status" in sample
    assert "youtube.com" in sample["resource_url"] or "youtu.be" in sample["resource_url"]

def test_resources_api_supports_catalog_mode():
    """Catalog mode returns strictly verified catalog items."""
    res = client.get("/api/resources?mode=catalog&query=Python")
    assert res.status_code == 200
    items = res.json()
    assert len(items) > 0
    assert all(item["is_verified_free"] is True for item in items)
    assert all(item["verification_status"].startswith("verified") for item in items)
