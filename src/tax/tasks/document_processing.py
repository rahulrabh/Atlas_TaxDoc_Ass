from celery import shared_task
from django.db import transaction

from tax.models import (
    Document,
    DocumentClassification,
    DocumentClassificationStatus,
)

from tax.services.document_classifier import DocumentClassifier
from tax.services.matching_engine import (
    match_classification_to_requirement,
)

@shared_task
def process_document(document_id):
    """
    Classify a document and attempt to match it
    against the tax case requirements.
    """

    document = (
        Document.objects
        .select_related("tax_case")
        .get(id=document_id)
    )

    classifier = DocumentClassifier()

    result = classifier.classify(document)

    with transaction.atomic():

        DocumentClassification.objects.filter(
            document=document,
            is_current=True,
        ).update(
            is_current=False,
        )

        classification = DocumentClassification.objects.create(
            document=document,
            document_type=result.document_type,
            tax_year=result.tax_year,
            person_id=result.person_id,
            employment_id=result.employment_id,
            confidence=result.confidence,
            status=result.status,
            is_current=True,
        )

        if result.status != DocumentClassificationStatus.CLASSIFIED:
            return str(classification.id)

        requirements = document.tax_case.requirements.all()

        for requirement in requirements:
            match_classification_to_requirement(
                classification=classification,
                requirement=requirement,
            )

    return str(classification.id)