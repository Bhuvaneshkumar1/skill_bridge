import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.data.catalog_manager import CatalogManager

client = TestClient(app)

REQUIRED_SUBJECT_KEYWORDS = [
    "python", "c++", "java", "javascript", "html", "react", "node", "sql", "data structures",
    "data analysis", "statistics", "machine learning", "deep learning", "generative ai",
    "agentic ai", "nlp", "computer vision", "cybersecurity", "ethical hacking",
    "network security", "web application security", "digital forensics", "cloud computing",
    "aws", "azure", "devops", "linux", "git", "api", "software testing", "ui/ux",
    "mobile application", "android", "react native", "data engineering", "computer networks",
    "operating systems", "system design", "interview preparation", "communication"
]

def test_catalog_has_at_least_40_entries():
    CatalogManager.reload_resources()
    resources = CatalogManager.get_resources()
    assert len(resources) >= 40, f"Expected at least 40 resources, got {len(resources)}"

def test_catalog_metadata_completeness_and_validity():
    CatalogManager.reload_resources()
    resources = CatalogManager.get_resources()
    ids = set()
    for res in resources:
        # Unique ID
        res_id = res.get("id")
        assert res_id not in ids, f"Duplicate ID found: {res_id}"
        ids.add(res_id)
        
        # Valid Title and Category
        assert res.get("title") and len(res.get("title")) > 3
        assert res.get("category") and len(res.get("category")) > 2
        
        # Valid Description
        assert res.get("description") and len(res.get("description")) > 10
        
        # Valid Prerequisites and Learning Objectives
        assert isinstance(res.get("prerequisite_skills"), list)
        assert isinstance(res.get("learning_objectives"), list)
        assert len(res.get("learning_objectives")) >= 2, f"Resource {res_id} has too few learning objectives"
        
        # Valid YouTube configuration
        url = res.get("resource_url", "")
        assert "youtube.com" in url or "youtu.be" in url
        assert res.get("channel_name") and len(res.get("channel_name")) > 1
        assert res.get("content_type") in ["video", "playlist", "channel"]
        assert res.get("verification_status") in [
            "verified_video", "verified_playlist", "verified_channel",
            "Verified YouTube Resource", "Verified YouTube Course"
        ]
        assert res.get("is_verified_free") is True

def test_all_required_subjects_covered():
    CatalogManager.reload_resources()
    resources = CatalogManager.get_resources()
    all_text = " ".join([
        f"{r.get('title', '')} {r.get('category', '')} {r.get('description', '')} {' '.join(r.get('skill_tags', []))}".lower()
        for r in resources
    ])
    
    missing = []
    for kw in REQUIRED_SUBJECT_KEYWORDS:
        if kw not in all_text:
            missing.append(kw)
    assert not missing, f"Missing required subjects from catalog: {missing}"

def test_catalog_search_across_metadata():
    CatalogManager.reload_resources()
    # Search by category
    results = CatalogManager.search_resources(query="Cloud Computing")
    assert len(results) > 0
    assert any("cloud" in (r.category or "").lower() or "cloud" in r.title.lower() for r in results)

    # Search by description keyword
    results_forensics = CatalogManager.search_resources(query="autopsy")
    assert len(results_forensics) > 0
    assert any("forensics" in (r.id or "") for r in results_forensics)

    # Search by skill tags
    results_dsa = CatalogManager.search_resources(query="binary search")
    assert len(results_dsa) > 0

def test_api_resources_catalog_mode_and_metadata_exposure():
    response = client.get("/api/resources?mode=catalog")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 40
    first = data[0]
    assert "category" in first
    assert "description" in first
    assert "prerequisite_skills" in first
    assert "learning_objectives" in first
    assert "channel_name" in first
    assert "content_type" in first

def test_unknown_topic_does_not_fail():
    response = client.get("/api/resources?topic=quantum_hyperdimensional_computing_xyz")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "youtube.com" in first["resource_url"]
    assert first["content_type"] == "search_fallback"
