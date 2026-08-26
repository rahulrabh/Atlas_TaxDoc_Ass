from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tax.models import TaxCase
from tax.services.document_review import (
    get_documents_for_review,
)


class DocumentReviewAPIView(APIView):

    def get(self, request, tax_case_id):
        tax_case = get_object_or_404(
            TaxCase,
            id=tax_case_id,
        )

        classifications = get_documents_for_review(
            tax_case
        )

        reviews = []

        for classification in classifications:
            reviews.append({
                "document_id": str(
                    classification.document.id
                ),
                "file_name": (
                    classification.document.file_name
                ),
                "document_type": (
                    classification.document_type
                ),
                "tax_year": classification.tax_year,
                "confidence": (
                    str(classification.confidence)
                    if classification.confidence is not None
                    else None
                ),
                "status": classification.status,
                "person_id": (
                    str(classification.person_id)
                    if classification.person_id
                    else None
                ),
                "employment_id": (
                    str(classification.employment_id)
                    if classification.employment_id
                    else None
                ),
            })

        return Response(
            {
                "tax_case_id": str(tax_case.id),
                "reviews": reviews,
            },
            status=status.HTTP_200_OK,
        )