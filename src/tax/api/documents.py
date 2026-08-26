from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tax.models import TaxCase
from tax.services.document_upload import (
    DuplicateDocumentError,
    upload_document,
)


class DocumentUploadAPIView(APIView):

    def post(self, request, tax_case_id):
        tax_case = get_object_or_404(
            TaxCase,
            id=tax_case_id,
        )

        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response(
                {"detail": "A file is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            document = upload_document(
                tax_case=tax_case,
                uploaded_file=uploaded_file,
            )

        except DuplicateDocumentError:
            return Response(
                {
                    "detail": (
                        "This document has already been uploaded."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                "id": str(document.id),
                "status": document.processing_status,
            },
            status=status.HTTP_202_ACCEPTED,
        )