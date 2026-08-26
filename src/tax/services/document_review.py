from decimal import Decimal

from django.db import transaction

from tax.models import (
    DocumentClassification,
    DocumentClassificationStatus,
    RequirementDocumentType,
)

from tax.services.matching_engine import (
    match_classification_to_requirement,
)

from tax.models import (
    DocumentClassification,
    DocumentClassificationStatus,
)


def get_documents_for_review(tax_case):
    return (
        DocumentClassification.objects
        .filter(
            document__tax_case=tax_case,
            status=DocumentClassificationStatus.REVIEW_REQUIRED,
            is_current=True,
        )
        .select_related(
            "document",
            "person",
            "employment",
        )
        .order_by("-created_at")
    )

@transaction.atomic
def resolve_document_review(
    classification,
    document_type,
    tax_year,
):
    """
    Resolve a review-required classification by creating
    a new confirmed classification while preserving history.
    """

    if classification.status != (
        DocumentClassificationStatus.REVIEW_REQUIRED
    ):
        return None

    if not classification.is_current:
        return None

    classification.is_current = False
    classification.save(
        update_fields=[
            "is_current",
            "updated_at",
        ]
    )

    new_classification = (
        DocumentClassification.objects.create(
            document=classification.document,
            document_type=document_type,
            tax_year=tax_year,
            person_id=classification.person_id,
            employment_id=classification.employment_id,
            confidence=Decimal("1.0000"),
            status=DocumentClassificationStatus.CLASSIFIED,
            is_current=True,
        )
    )

    requirements = classification.document.tax_case.requirements.all()

    for requirement in requirements:
        match_classification_to_requirement(
            classification=new_classification,
            requirement=requirement,
        )

    return new_classification