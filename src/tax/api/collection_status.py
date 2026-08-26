from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tax.models import TaxCase
from tax.services.collection_status import get_collection_status


class CollectionStatusAPIView(APIView):

    def get(self, request, tax_case_id):
        tax_case = get_object_or_404(
            TaxCase,
            id=tax_case_id,
        )

        result = get_collection_status(tax_case)

        requirements = []

        for item in result["requirements"]:
            requirement = item["requirement"]

            requirements.append({
                "requirement_id": str(
                    requirement.id
                ),
                "document_type": requirement.document_type,
                "tax_year": requirement.tax_year,
                "status": item["status"],
            })

        return Response(
            {
                "tax_case_id": str(tax_case.id),
                "summary": result["summary"],
                "requirements": requirements,
                "needs_review": result["summary"]["needs_review"],
            },
            status=status.HTTP_200_OK,
        )