from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tax.models import (
    Document,
    RequirementDocumentType,
)

from tax.services.document_review import (
    resolve_document_review,
)


class DocumentReviewResolutionAPIView(APIView):

    def patch(self, request, document_id):
        document = get_object_or_404(
            Document,
            id=document_id,
        )

        document_type = request.data.get(
            "document_type"
        )

        tax_year = request.data.get(
            "tax_year"
        )

        if not document_type or not tax_year:
            return Response(
                {
                    "detail": (
                        "document_type and tax_year are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if document_type not in RequirementDocumentType.values:
            return Response(
                {
                    "detail": "Invalid document_type."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tax_year = int(tax_year)
        except (TypeError, ValueError):
            return Response(
                {
                    "detail": "tax_year must be an integer."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        classification = (
            document.classifications
            .filter(is_current=True)
            .first()
        )

        if not classification:
            return Response(
                {
                    "detail": (
                        "No current classification found."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = resolve_document_review(
            classification=classification,
            document_type=document_type,
            tax_year=tax_year,
        )

        if result is None:
            return Response(
                {
                    "detail": (
                        "Document is not currently "
                        "awaiting review."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "classification_id": str(
                    result.id
                ),
                "document_id": str(
                    document.id
                ),
                "document_type": result.document_type,
                "tax_year": result.tax_year,
                "confidence": str(
                    result.confidence
                ),
                "status": result.status,
            },
            status=status.HTTP_200_OK,
        )