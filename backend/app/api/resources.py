from fastapi import APIRouter, Query
from typing import List, Optional
from backend.app.schemas import LearningResource, ResourceSearchQuery
from backend.app.data.catalog_manager import CatalogManager

router = APIRouter(prefix="/resources", tags=["Learning Resource Finder"])

@router.get("", response_model=List[LearningResource])
def search_resources(
    query: Optional[str] = Query(None, description="Keywords to search in title, provider, or tags"),
    skill: Optional[str] = Query(None, description="Filter by skill tag (e.g. Python, SQL)"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (Beginner, Intermediate, Advanced)"),
    resource_type: Optional[str] = Query(None, description="Filter by type (video, documentation, interactive_course)")
):
    """
    Returns verified free learning resources matching filters.
    All returned resources have verified URL and cost information.
    """
    return CatalogManager.search_resources(
        query=query,
        skill=skill,
        difficulty=difficulty,
        resource_type=resource_type
    )

@router.post("/search", response_model=List[LearningResource])
def post_search_resources(search_body: ResourceSearchQuery):
    """
    POST body resource search for complex query objects.
    """
    return CatalogManager.search_resources(
        query=search_body.query,
        skill=search_body.skill,
        difficulty=search_body.difficulty,
        resource_type=search_body.resource_type
    )
