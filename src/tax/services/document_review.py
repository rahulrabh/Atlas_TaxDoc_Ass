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