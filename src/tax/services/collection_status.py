from tax.models import (
    DocumentClassificationStatus,
    Requirement,
    RequirementDocumentMatch,
    DocumentClassification
)

def get_collection_status(tax_case):
    requirements = Requirement.objects.filter(
        tax_case=tax_case,
    ).select_related(
        "person",
        "employment",
    )

    result = []

    for requirement in requirements:
        active_match = (
            RequirementDocumentMatch.objects
            .filter(
                requirement=requirement,
                is_active=True,
            )
            .select_related(
                "document",
                "classification",
            )
            .first()
        )

        if active_match:
            status = "RECEIVED"
        else:
            status = "OUTSTANDING"

        result.append({
            "requirement": requirement,
            "status": status,
            "match": active_match,
        })

    reviews = (
        DocumentClassification.objects
        .filter(
            document__tax_case=tax_case,
            status=DocumentClassificationStatus.REVIEW_REQUIRED,
        )
        .select_related(
            "document",
            "person",
            "employment",
        )
    )

    received = sum(
        1 for item in result
        if item["status"] == "RECEIVED"
    )

    outstanding = sum(
        1 for item in result
        if item["status"] == "OUTSTANDING"
    )

    return {
        "summary": {
            "total": len(result),
            "received": received,
            "outstanding": outstanding,
            "needs_review": reviews.count(),
        },
        "requirements": result,
        "reviews": reviews,
    }