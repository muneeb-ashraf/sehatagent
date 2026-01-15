# Knowledge Package
"""
Health Knowledge Base for SehatAgent

Data Sources:
- WHO Global Health Data (https://www.who.int/data)
- Pakistan Bureau of Statistics (https://pslm-sdgs.data.gov.pk/health/index)
- NIH Open Clinical Data (https://www.ncbi.nlm.nih.gov/gap)
- Open Food Facts (https://world.openfoodfacts.org/data)
"""

from app.knowledge.health_knowledge_base import (
    WHO_HEALTH_DATA,
    PAKISTAN_HEALTH_STATISTICS,
    PAKISTAN_NUTRITION_DATA,
    NIH_CLINICAL_PATTERNS,
    EMERGENCY_CONTACTS_PAKISTAN,
    get_all_knowledge
)

__all__ = [
    "WHO_HEALTH_DATA",
    "PAKISTAN_HEALTH_STATISTICS",
    "PAKISTAN_NUTRITION_DATA",
    "NIH_CLINICAL_PATTERNS",
    "EMERGENCY_CONTACTS_PAKISTAN",
    "get_all_knowledge"
]
