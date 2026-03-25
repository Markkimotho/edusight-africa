"""
Teaching resources endpoint — static catalogue served in-process.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()

# ---------------------------------------------------------------------------
# Static resource catalogue
# In a real deployment this would live in the database.
# ---------------------------------------------------------------------------
RESOURCES: list[dict] = [
    {
        "id": "res-001",
        "title": "Early Reading Strategies for Grade 1-3",
        "category": "literacy",
        "language": "en",
        "level": "primary",
        "description": "A guide for teachers on phonics, sight words, and early fluency interventions.",
        "url": "https://example.com/resources/early-reading",
        "tags": ["reading", "phonics", "grade-1", "grade-2", "grade-3"],
    },
    {
        "id": "res-002",
        "title": "Math Foundations: Number Sense Activities",
        "category": "mathematics",
        "language": "en",
        "level": "primary",
        "description": "Hands-on activities to build number sense in early primary learners.",
        "url": "https://example.com/resources/math-number-sense",
        "tags": ["math", "number-sense", "activity"],
    },
    {
        "id": "res-003",
        "title": "Mbinu za Kusoma kwa Darasa la 1-3 (Kiswahili)",
        "category": "literacy",
        "language": "sw",
        "level": "primary",
        "description": "Mwongozo wa walimu kuhusu mbinu za kusoma kwa watoto wadogo.",
        "url": "https://example.com/resources/kusoma-darasa",
        "tags": ["kusoma", "darasa-1", "darasa-2", "kiswahili"],
    },
    {
        "id": "res-004",
        "title": "Attendance Improvement Parent Handbook",
        "category": "attendance",
        "language": "en",
        "level": "all",
        "description": "Practical strategies for parents to support regular school attendance.",
        "url": "https://example.com/resources/attendance-handbook",
        "tags": ["attendance", "parent", "handbook"],
    },
    {
        "id": "res-005",
        "title": "Behavioural Support: Classroom Management Techniques",
        "category": "behavioral",
        "language": "en",
        "level": "all",
        "description": "Evidence-based classroom management approaches for African school contexts.",
        "url": "https://example.com/resources/classroom-management",
        "tags": ["behavior", "classroom", "teacher"],
    },
    {
        "id": "res-006",
        "title": "Mathématiques de Base pour les CP-CE2 (Français)",
        "category": "mathematics",
        "language": "fr",
        "level": "primary",
        "description": "Activités de numération et de calcul pour les élèves de CP à CE2.",
        "url": "https://example.com/resources/maths-cp-ce2",
        "tags": ["maths", "cp", "ce2", "francais"],
    },
    {
        "id": "res-007",
        "title": "Special Needs: Inclusive Classroom Practices",
        "category": "inclusion",
        "language": "en",
        "level": "all",
        "description": "Guidance for teachers on supporting learners with diverse needs.",
        "url": "https://example.com/resources/inclusion",
        "tags": ["inclusion", "special-needs", "diversity"],
    },
    {
        "id": "res-008",
        "title": "Home Learning Guide for Parents",
        "category": "home-support",
        "language": "en",
        "level": "all",
        "description": "How parents can support homework, reading, and learning at home.",
        "url": "https://example.com/resources/home-learning",
        "tags": ["parent", "homework", "home-learning"],
    },
]


@router.get("/")
async def list_resources(
    current_user: User = Depends(get_current_active_user),
    category: str | None = Query(default=None, description="Filter by category"),
    language: str | None = Query(default=None, description="Filter by language code (en, sw, fr, …)"),
    level: str | None = Query(default=None, description="Filter by level (primary, secondary, all)"),
) -> dict:
    """
    Return the list of teaching/parent resources.

    Filters:
        category: literacy | mathematics | attendance | behavioral | inclusion | home-support
        language: en | sw | fr | …
        level:    primary | secondary | all
    """
    results = RESOURCES

    if category:
        results = [r for r in results if r["category"] == category]
    if language:
        results = [r for r in results if r["language"] == language]
    if level:
        results = [r for r in results if r["level"] == level]

    return {
        "data": results,
        "meta": {
            "total": len(results),
            "filters_applied": {
                "category": category,
                "language": language,
                "level": level,
            },
        },
    }
