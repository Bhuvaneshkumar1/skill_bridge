from fastapi import APIRouter, Query
from typing import List, Optional
from backend.app.schemas import LearningResource, ResourceSearchQuery
from backend.app.data.catalog_manager import CatalogManager
from backend.app.tools.resource_tools import find_free_learning_resources

router = APIRouter(prefix="/resources", tags=["Learning Resource Finder"])

@router.get("", response_model=List[LearningResource])
def search_resources(
    query: Optional[str] = Query(None, description="Keywords to search in title, provider, or tags"),
    topic: Optional[str] = Query(None, description="Topic or subject keyword alias"),
    skill: Optional[str] = Query(None, description="Filter by skill tag (e.g. Python, SQL)"),
    career: Optional[str] = Query(None, description="Filter by target career (e.g. Python Developer)"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (Beginner, Intermediate, Advanced)"),
    resource_type: Optional[str] = Query(None, description="Filter by type (video, playlist, channel, interactive_course)"),
    mode: Optional[str] = Query("all", description="Search mode: 'catalog', 'youtube', or 'all'")
):
    """
    Returns learning resources matching filters.
    - 'catalog': Returns verified YouTube courses from local curated catalog.
    - 'all' / 'youtube': Returns verified catalog items + live YouTube discovery + search fallbacks.
    """
    effective_query = query or topic
    if mode == "catalog":
        return CatalogManager.search_resources(
            query=effective_query,
            skill=skill,
            career=career,
            difficulty=difficulty,
            resource_type=resource_type
        )

    raw_items = find_free_learning_resources(
        skill=skill,
        career=career,
        difficulty=difficulty,
        query=effective_query
    )

    results: List[LearningResource] = []
    for item in raw_items:
        if resource_type and item.get("resource_type") != resource_type and item.get("content_type") != resource_type:
            continue
        try:
            results.append(LearningResource(**item))
        except Exception:
            pass

    return results

@router.post("/search", response_model=List[LearningResource])
def post_search_resources(search_body: ResourceSearchQuery):
    """
    POST body resource search for complex query objects.
    """
    effective_query = search_body.query or search_body.topic
    if search_body.mode == "catalog":
        return CatalogManager.search_resources(
            query=effective_query,
            skill=search_body.skill,
            career=search_body.career,
            difficulty=search_body.difficulty,
            resource_type=search_body.resource_type
        )

    raw_items = find_free_learning_resources(
        skill=search_body.skill,
        career=search_body.career,
        difficulty=search_body.difficulty,
        query=effective_query
    )

    results: List[LearningResource] = []
    for item in raw_items:
        if search_body.resource_type and item.get("resource_type") != search_body.resource_type and item.get("content_type") != search_body.resource_type:
            continue
        try:
            results.append(LearningResource(**item))
        except Exception:
            pass

    return results
