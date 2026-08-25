from decimal import Decimal
from django.db import transaction

from tax.models import (
    DocumentClassificationStatus,
    RequirementDocumentMatch,
    RequirementDocumentMatchStatus,
)


CONFIDENCE_THRESHOLD = Decimal("0.8000")


def matches_requirement(classification, requirement):
    """
    Determine whether a classification satisfies a requirement.
    """

    # 1. Classification must be the current interpretation
    if not classification.is_current:
        return False

    # 2. Classification must be successfully classified
    if classification.status != DocumentClassificationStatus.CLASSIFIED:
        return False

    # 3. Classification must have sufficient confidence
    if (
        classification.confidence is None
        or classification.confidence < CONFIDENCE_THRESHOLD
    ):
        return False

    # 4. Document type must match
    if classification.document_type != requirement.document_type:
        return False

    # 5. Tax year must match
    if classification.tax_year != requirement.tax_year:
        return False

    # 6. Person scope must match
    if classification.person_id != requirement.person_id:
        return False

    # 7. Employment scope must match
    if classification.employment_id != requirement.employment_id:
        return False

    return True

@transaction.atomic
def match_classification_to_requirement(
    classification,
    requirement,
):
    """
    Match a classification against a requirement and persist
    the resulting active match.
    """

    if not matches_requirement(classification, requirement):
        return None

    existing_active_match = (
        RequirementDocumentMatch.objects
        .filter(
            requirement=requirement,
            is_active=True,
        )
        .first()
    )

    if existing_active_match:
        existing_active_match.is_active = False
        existing_active_match.status = (
            RequirementDocumentMatchStatus.SUPERSEDED
        )
        existing_active_match.save(
            update_fields=[
                "is_active",
                "status",
                "updated_at",
            ]
        )

    return RequirementDocumentMatch.objects.create(
        requirement=requirement,
        document=classification.document,
        classification=classification,
        status=RequirementDocumentMatchStatus.MATCHED,
        is_active=True,
        match_reason=(
            "Document classification matches requirement "
            "with sufficient confidence."
        ),
    )